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

"""This package contains a scaffold of a model."""

from typing import Any, Callable, Dict

from aea.skills.base import Model


class Requests(Model):
    """Keep the current pending requests."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, **kwargs)

        # mapping from dialogue reference nonce to a callback
        self.request_id_to_callback: Dict[str, Callable] = {}
