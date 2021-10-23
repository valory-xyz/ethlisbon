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

import json
from typing import Any, Callable, Dict, Optional, Tuple, cast

from aea.protocols.dialogue.base import Dialogue
from aea.skills.base import Behaviour

from packages.collectooor.contracts.artblocks.contract import ArtBlocksContract
from packages.collectooor.skills.monitor.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    HttpDialogue,
    HttpDialogues,
)
from packages.collectooor.skills.monitor.models import Requests
from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.fetchai.connections.ledger.base import CONNECTION_ID as LEDGER_API_ADDRESS
from packages.fetchai.protocols.contract_api import ContractApiMessage
from packages.fetchai.protocols.http import HttpMessage
from packages.fetchai.protocols.signing.custom_types import Terms


class Monitoring(Behaviour):
    """This class scaffolds a behaviour."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Init the monitoring behaviour."""
        super().__init__(*args, **kwargs)
        self.active_project: Optional[int] = None
        self.is_request_in_flight = False
        self.artblocks_contract = "0x1cd623a86751d4c4f20c96000fec763941f098a2"

    def setup(self) -> None:
        """Implement the setup."""

    def act(self) -> None:
        """Implement the act."""
        if self.active_project is None:
            self.find_active_project()

    def teardown(self) -> None:
        """Implement the task teardown."""

    def find_active_project(self) -> None:
        """Find the active artblock project with the highest project id."""
        if not self.is_request_in_flight:
            self.send_contract_api_request(
                request_callback=self.handle_active_project_id,
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
                contract_address=self.artblocks_contract,
                contract_id=str(ArtBlocksContract.contract_id),
                contract_callable="active_project_id",
            )

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
        if not message.performative == ContractApiMessage.Performative.STATE:
            raise ValueError("wrong performative")
        self.active_project = cast(int, message.state.body["project_id"])

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
