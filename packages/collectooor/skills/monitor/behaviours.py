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

"""This package contains a scaffold of a behaviour."""

import binascii
import json
from typing import Any, Callable, Dict, Optional, Tuple, cast

from aea.protocols.dialogue.base import Dialogue
from aea.skills.base import Behaviour

from packages.collectooor.contracts.artblocks.contract import ArtBlocksContract
from packages.collectooor.contracts.artblocks_periphery.contract import (
    ArtBlocksPeripheryContract,
)
from packages.collectooor.skills.monitor.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    HttpDialogue,
    HttpDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.collectooor.skills.monitor.models import Requests
from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.fetchai.connections.ledger.base import CONNECTION_ID as LEDGER_API_ADDRESS
from packages.fetchai.protocols.contract_api import ContractApiMessage
from packages.fetchai.protocols.http import HttpMessage
from packages.fetchai.protocols.ledger_api import LedgerApiMessage
from packages.fetchai.protocols.signing import SigningMessage
from packages.fetchai.protocols.signing.custom_types import (
    RawMessage,
    RawTransaction,
    SignedTransaction,
    Terms,
)
from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract


class Monitoring(Behaviour):  # pylint: disable=too-many-instance-attributes
    """This class scaffolds a behaviour."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Init the monitoring behaviour."""
        super().__init__(*args, **kwargs)
        self.max_eth_in_wei = 1000000000000000000
        self.starting_id: Optional[int] = None
        self.active_project: Optional[int] = None
        self.project_details: Optional[dict] = None
        self.is_request_in_flight = False
        self.artblocks_contract = "0x1CD623a86751d4C4f20c96000FEC763941f098A2"
        self.artblocks_periphery_contract = "0x58727f5Fc3705C30C9aDC2bcCC787AB2BA24c441"
        self.safe_contract = "0x2caB92c1E9D2a701Ca0411b0ff35A0907Ca31F7f"
        self.data: Optional[bytes] = None
        self.gnosis_hash: Optional[str] = None
        self.signed_message: Optional[str] = None
        self.raw_transaction: Optional[RawTransaction] = None
        self.signed_transaction: Optional[SignedTransaction] = None
        self.tx_digest: Optional[str] = None

    def setup(self) -> None:
        """Implement the setup."""

    def act(self) -> None:
        """Implement the act."""
        if self.active_project is None and not self.is_request_in_flight:
            self.send_contract_api_request(
                request_callback=self.handle_active_project_id,
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=self.artblocks_contract,
                contract_id=str(ArtBlocksContract.contract_id),
                contract_callable="get_active_project",
                starting_id=self.starting_id,
            )
        if (
            self.active_project is not None
            and self.data is None
            and not self.is_request_in_flight
        ):
            self.send_contract_api_request(
                request_callback=self.handle_purchase_data,
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=self.artblocks_periphery_contract,
                contract_id=str(ArtBlocksPeripheryContract.contract_id),
                contract_callable="purchase_data",
                project_id=self.active_project,
            )
        if (
            self.data is not None
            and self.project_details is not None
            and self.gnosis_hash is None
            and not self.is_request_in_flight
        ):
            self.send_contract_api_request(
                request_callback=self.handle_gnosis_hash,
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=self.safe_contract,
                contract_id=str(GnosisSafeContract.contract_id),
                contract_callable="get_raw_safe_transaction_hash",
                to_address=self.artblocks_periphery_contract,
                value=self.project_details["price_per_token_in_wei"],
                data=self.data,
            )
        if (
            self.gnosis_hash is not None
            and self.signed_message is None
            and not self.is_request_in_flight
        ):
            safe_tx_hash_bytes = binascii.unhexlify(self.gnosis_hash)
            self.send_signing_request(
                request_callback=self.handle_signing_message_response,
                raw_message=safe_tx_hash_bytes,
                is_deprecated_mode=True,
            )
        if (
            self.signed_message is not None
            and self.project_details is not None
            and self.raw_transaction is None
            and not self.is_request_in_flight
        ):
            self.send_contract_api_request(
                request_callback=self.handle_gnosis_tx,
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.safe_contract,
                contract_id=str(GnosisSafeContract.contract_id),
                contract_callable="get_raw_safe_transaction",
                sender_address=self.context.agent_address,
                owners=(self.context.agent_address,),
                to_address=self.artblocks_periphery_contract,
                value=self.project_details["price_per_token_in_wei"],
                data=self.data,
                signatures_by_owner={self.context.agent_address: self.signed_message},
            )
        if (
            self.raw_transaction is not None
            and self.signed_transaction is None
            and not self.is_request_in_flight
        ):
            self.send_transaction_signing_request(
                request_callback=self.handle_signing_transaction_response,
                raw_transaction=self.raw_transaction,
            )
        if self.signed_transaction is not None and not self.is_request_in_flight:
            self.send_transaction_request(
                request_callback=self.handle_transaction_response,
                signed_transaction=self.signed_transaction,
            )

    def teardown(self) -> None:
        """Implement the task teardown."""

    def send_contract_api_request(  # pylint: disable=too-many-arguments
        self,
        request_callback: Callable,
        performative: ContractApiMessage.Performative,
        contract_address: Optional[str],
        contract_id: str,
        contract_callable: str,
        **kwargs: Any,
    ) -> None:
        """
        Request contract safe transaction hash

        :param request_callback: the request callback handler
        :param performative: the message performative
        :param contract_address: the contract address
        :param contract_id: the contract id
        :param contract_callable: the collable to call on the contract
        :param kwargs: keyword argument for the contract api request
        """
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        kwargs = {
            "performative": performative,
            "counterparty": str(LEDGER_API_ADDRESS),
            "ledger_id": self.context.default_ledger_id,
            "contract_id": contract_id,
            "callable": contract_callable,
            "kwargs": ContractApiMessage.Kwargs(kwargs),
        }
        if contract_address is not None:
            kwargs["contract_address"] = contract_address
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            **kwargs
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            contract_api_dialogue,
        )
        contract_api_dialogue.terms = self._get_default_terms()
        request_nonce = self._get_request_nonce_from_dialogue(contract_api_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = request_callback
        self.context.outbox.put_message(message=contract_api_msg)
        self.is_request_in_flight = True

    def handle_active_project_id(self, message: ContractApiMessage) -> None:
        """Callback handler for the active project id request."""
        self.is_request_in_flight = False
        if not message.performative == ContractApiMessage.Performative.STATE:
            raise ValueError("wrong performative")
        project_id = cast(Optional[int], message.state.body["project_id"])
        if project_id is None:
            return
        project_details = message.state.body
        if not self.is_acceptable_project(project_details):
            self.context.logger.info(
                f"found unsuitable project: {project_details}. Continue searching..."
            )
            self.starting_id = project_id
            return
        self.active_project = project_id
        self.project_details = project_details
        self.context.logger.info(f"found suitable project: {self.project_details}.")

    def is_acceptable_project(self, project_details: dict) -> bool:
        """Check if we can accept the project."""
        # very simplified atm, just checking for price to be max 1 ETH
        return project_details["price_per_token_in_wei"] <= self.max_eth_in_wei

    def handle_purchase_data(self, message: ContractApiMessage) -> None:
        """Callback handler for the purchase data request."""
        self.is_request_in_flight = False
        if not message.performative == ContractApiMessage.Performative.STATE:
            raise ValueError("wrong performative")
        data = cast(Optional[bytes], message.state.body["data"])
        self.data = data
        self.context.logger.info(f"found data: {str(self.data)}")

    def handle_gnosis_hash(self, message: ContractApiMessage) -> None:
        """Callback handler for the gnosis hash request."""
        self.is_request_in_flight = False
        if not message.performative == ContractApiMessage.Performative.STATE:
            raise ValueError("wrong performative")
        gnosis_hash = cast(str, message.state.body["tx_hash"])
        self.gnosis_hash = gnosis_hash[2:]
        self.context.logger.info(f"found tx_hash: {self.gnosis_hash}")

    def handle_gnosis_tx(self, message: ContractApiMessage) -> None:
        """Callback handler for the gnosis tx request."""
        self.is_request_in_flight = False
        if not message.performative == ContractApiMessage.Performative.RAW_TRANSACTION:
            raise ValueError("wrong performative")
        raw_tx = message.raw_transaction
        self.raw_transaction = raw_tx
        self.context.logger.info(f"found raw transaciton: {self.raw_transaction}")

    @classmethod
    def _get_request_nonce_from_dialogue(cls, dialogue: Dialogue) -> str:
        """Get the request nonce for the request, from the protocol's dialogue."""
        return dialogue.dialogue_label.dialogue_reference[0]

    def _get_default_terms(self) -> Terms:
        """
        Get default transaction terms.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.context.default_ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        return terms

    def _build_http_request_message(  # pylint: disable=too-many-arguments
        self,
        method: str,
        url: str,
        content: Dict = None,
        headers: Dict = None,
        parameters: Dict = None,
    ) -> Tuple[HttpMessage, HttpDialogue]:
        """
        Send an http request message from the skill context.

        This method is skill-specific, and therefore
        should not be used elsewhere.

        :param method: the http request method (i.e. 'GET' or 'POST').
        :param url: the url to send the message to.
        :param content: the payload.
        :param headers: headers to be included.
        :param parameters: url query parameters.
        :return: the http message and the http dialogue
        """
        if parameters:
            url = url + "?"
            for key, val in parameters.items():
                url += f"{key}={val}&"
            url = url[:-1]

        header_string = ""
        if headers:
            for key, val in headers.items():
                header_string += f"{key}: {val}\r\n"

        # context
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)

        # http request message
        request_http_message, http_dialogue = http_dialogues.create(
            counterparty=str(HTTP_CLIENT_PUBLIC_ID),
            performative=HttpMessage.Performative.REQUEST,
            method=method,
            url=url,
            headers=header_string,
            version="",
            body=b"" if content is None else json.dumps(content).encode("utf-8"),
        )
        request_http_message = cast(HttpMessage, request_http_message)
        http_dialogue = cast(HttpDialogue, http_dialogue)
        return request_http_message, http_dialogue

    def send_signing_request(
        self,
        request_callback: Callable,
        raw_message: bytes,
        is_deprecated_mode: bool = False,
    ) -> None:
        """Send a signing request."""
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            raw_message=RawMessage(
                self.context.default_ledger_id,
                raw_message,
                is_deprecated_mode=is_deprecated_mode,
            ),
            terms=Terms(
                ledger_id=self.context.default_ledger_id,
                sender_address="",
                counterparty_address="",
                amount_by_currency_id={},
                quantities_by_good_id={},
                nonce="",
            ),
        )
        request_nonce = self._get_request_nonce_from_dialogue(signing_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = request_callback
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.is_request_in_flight = True

    def handle_signing_message_response(self, message: SigningMessage) -> None:
        """Callback handler for the gnosis hash request."""
        self.is_request_in_flight = False
        if not message.performative == SigningMessage.Performative.SIGNED_MESSAGE:
            raise ValueError("wrong performative")
        signed_message = cast(str, message.signed_message.body)
        self.signed_message = signed_message[2:]
        self.context.logger.info(f"found signed_message: {self.signed_message}")

    def send_transaction_signing_request(
        self,
        request_callback: Callable,
        raw_transaction: RawTransaction,
    ) -> None:
        """Send a transaction signing request."""
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        terms = Terms(
            self.context.default_ledger_id,
            self.context.agent_address,
            counterparty_address="",
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            raw_transaction=raw_transaction,
            terms=terms,
        )
        signing_dialogue = cast(SigningDialogue, signing_dialogue)
        request_nonce = self._get_request_nonce_from_dialogue(signing_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = request_callback
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.is_request_in_flight = True

    def handle_signing_transaction_response(self, message: SigningMessage) -> None:
        """Callback handler for the gnosis hash request."""
        self.is_request_in_flight = False
        if not message.performative == SigningMessage.Performative.SIGNED_TRANSACTION:
            raise ValueError("wrong performative")
        signed_transaction = message.signed_transaction
        self.signed_transaction = signed_transaction
        self.context.logger.info(f"found signed_transaction: {self.signed_transaction}")

    def send_transaction_request(
        self, request_callback: Callable, signed_transaction: SignedTransaction
    ) -> None:
        """Send a transaction request."""
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_msg, ledger_api_dialogue = ledger_api_dialogues.create(
            counterparty=str(LEDGER_API_ADDRESS),
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            signed_transaction=signed_transaction,
        )
        ledger_api_dialogue = cast(LedgerApiDialogue, ledger_api_dialogue)
        request_nonce = self._get_request_nonce_from_dialogue(ledger_api_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = request_callback
        self.context.outbox.put_message(message=ledger_api_msg)
        self.is_request_in_flight = True

    def handle_transaction_response(self, message: LedgerApiMessage) -> None:
        """Callback handler for the gnosis hash request."""
        self.is_request_in_flight = False
        if not message.performative == LedgerApiMessage.Performative.TRANSACTION_DIGEST:
            raise ValueError("wrong performative")
        tx_digest = cast(Optional[str], message.transaction_digest.body)
        self.tx_digest = tx_digest
        self.context.logger.info(f"found signed_transaction: {self.tx_digest}")

    def send_transaction_receipt_request(
        self, request_callback: Callable, ledger_api_msg_: LedgerApiMessage
    ) -> None:
        """Send a transaction receipt request."""
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_msg, ledger_api_dialogue = ledger_api_dialogues.create(
            counterparty=str(LEDGER_API_ADDRESS),
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
            transaction_digest=ledger_api_msg_.transaction_digest,
        )
        ledger_api_dialogue = cast(LedgerApiDialogue, ledger_api_dialogue)
        request_nonce = self._get_request_nonce_from_dialogue(ledger_api_dialogue)
        cast(Requests, self.context.requests).request_id_to_callback[
            request_nonce
        ] = request_callback
        self.context.outbox.put_message(message=ledger_api_msg)
        self.context.logger.info("sending transaction receipt request.")
