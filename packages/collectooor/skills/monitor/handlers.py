# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Handlers for the collectooor."""

from abc import ABC
from typing import FrozenSet, Optional, cast

from aea.configurations.data_types import PublicId
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, Dialogues
from aea.skills.base import Handler

from packages.collectooor.skills.monitor.models import Requests
from packages.fetchai.protocols.contract_api import ContractApiMessage
from packages.fetchai.protocols.http import HttpMessage
from packages.fetchai.protocols.ledger_api import LedgerApiMessage
from packages.fetchai.protocols.signing import SigningMessage


class AbstractResponseHandler(Handler, ABC):
    """
    Abstract response Handler.

    This abstract handler works in tandem with the 'Requests' model.
    Whenever a message of 'response' type arrives, the handler
    tries to dispatch it to a pending request previously registered
    in 'Requests' by some other code in the same skill.

    The concrete classes must set the 'allowed_response_performatives'
    class attribute to the (frozen)set of performative the developer
    wants the handler to handle.
    """

    allowed_response_performatives: FrozenSet[Message.Performative]

    def setup(self) -> None:
        """Set up the handler."""

    def teardown(self) -> None:
        """Tear down the handler."""

    def handle(self, message: Message) -> None:
        """
        Handle the response message.

        Steps:
            1. Try to recover the 'dialogues' instance, for the protocol of this handler,
                from the skill context. The attribute name used to read the attribute
                is computed by '_get_dialogues_attribute_name()' method.
                If no dialogues instance is found, log a message and return.
            2. Try to recover the dialogue; if no dialogue is present, log a message and return.
            3. Check whether the performative is in the set of allowed performative;
                if not, log a message and return.
            4. Try to recover the callback of the request associated to the response
                from the 'Requests' model; if no callback is present, log a message and return.
            5. If the above check have passed, then call the callback with the received message.

        :param message: the message to handle.
        """
        protocol_dialogues = self._recover_protocol_dialogues()
        if protocol_dialogues is None:
            self._handle_missing_dialogues()
            return
        protocol_dialogues = cast(Dialogues, protocol_dialogues)

        protocol_dialogue = cast(Optional[Dialogue], protocol_dialogues.update(message))
        if protocol_dialogue is None:
            self._handle_unidentified_dialogue(message)
            return

        if message.performative not in self.allowed_response_performatives:
            self._handle_unallowed_performative(message)
            return

        request_nonce = protocol_dialogue.dialogue_label.dialogue_reference[0]
        callback = cast(Requests, self.context.requests).request_id_to_callback.pop(
            request_nonce, None
        )
        if callback is None:
            self._handle_no_callback(message, protocol_dialogue)
            return

        self._log_message_handling(message)
        callback(message)

    def _get_dialogues_attribute_name(self) -> str:
        """
        Get dialogues attribute name.

        By convention, the Dialogues model of the skill follows
        the template '{protocol_name}_dialogues'.

        Override this method accordingly if the name of hte Dialogues
        model is different.

        :return: the dialogues attribute name.
        """
        return cast(PublicId, self.SUPPORTED_PROTOCOL).name + "_dialogues"

    def _recover_protocol_dialogues(self) -> Optional[Dialogues]:
        """
        Recover protocol dialogues from supported protocol id.

        :return: the dialogues, or None if the dialogues object was not found.
        """
        attribute = self._get_dialogues_attribute_name()
        return getattr(self.context, attribute, None)

    def _handle_missing_dialogues(self) -> None:
        """Handle missing dialogues in context."""
        expected_attribute_name = self._get_dialogues_attribute_name()
        self.context.logger.info(
            "cannot find Dialogues object in skill context with attribute name: %s",
            expected_attribute_name,
        )

    def _handle_unidentified_dialogue(self, message: Message) -> None:
        """
        Handle an unidentified dialogue.

        :param message: the unidentified message to be handled
        """
        self.context.logger.info(
            "received invalid message: unidentified dialogue. message=%s", message
        )

    def _handle_unallowed_performative(self, message: Message) -> None:
        """
        Handle a message with an unallowed response performative.

        Log an error message saying that the handler did not expect requests
        but only responses.

        :param message: the message
        """
        self.context.logger.warning(
            "received invalid message: unallowed performative. message=%s.", message
        )

    def _handle_no_callback(self, _message: Message, dialogue: Dialogue) -> None:
        """
        Handle no callback found.

        :param _message: the message to be handled
        :param dialogue: the http dialogue
        """
        request_nonce = dialogue.dialogue_label.dialogue_reference[0]
        self.context.logger.warning(
            f"callback not specified for request with nonce {request_nonce}"
        )

    def _log_message_handling(self, message: Message) -> None:
        """Log the handling of the message."""
        self.context.logger.info("calling registered callback with message=%s", message)


class HttpHandler(AbstractResponseHandler):
    """The HTTP response handler."""

    SUPPORTED_PROTOCOL: Optional[PublicId] = HttpMessage.protocol_id
    allowed_response_performatives = frozenset({HttpMessage.Performative.RESPONSE})


class SigningHandler(AbstractResponseHandler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL: Optional[PublicId] = SigningMessage.protocol_id
    allowed_response_performatives = frozenset(
        {
            SigningMessage.Performative.SIGNED_MESSAGE,
            SigningMessage.Performative.SIGNED_TRANSACTION,
            SigningMessage.Performative.ERROR,
        }
    )


class LedgerApiHandler(AbstractResponseHandler):
    """Implement the ledger handler."""

    SUPPORTED_PROTOCOL: Optional[PublicId] = LedgerApiMessage.protocol_id
    allowed_response_performatives = frozenset(
        {
            LedgerApiMessage.Performative.BALANCE,
            LedgerApiMessage.Performative.RAW_TRANSACTION,
            LedgerApiMessage.Performative.TRANSACTION_DIGEST,
            LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
            LedgerApiMessage.Performative.ERROR,
        }
    )


class ContractApiHandler(AbstractResponseHandler):
    """Implement the contract api handler."""

    SUPPORTED_PROTOCOL: Optional[PublicId] = ContractApiMessage.protocol_id
    allowed_response_performatives = frozenset(
        {
            ContractApiMessage.Performative.RAW_TRANSACTION,
            ContractApiMessage.Performative.RAW_MESSAGE,
            ContractApiMessage.Performative.ERROR,
            ContractApiMessage.Performative.STATE,
        }
    )
