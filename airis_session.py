import requests
import random
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Type

from uagents.communication import send_message, send_sync_message
from uagents.models import Model
from uagents.crypto import Identity


class AbstractAirisSession(ABC):
    @abstractmethod
    def initialize_session(self, goal, actions) -> str | None:
        pass

    @abstractmethod
    def pre_action(self, environment_state) -> tuple[str, str, str]:
        pass

    @abstractmethod
    def post_action(self, environment_state) -> dict | None:
        pass

    @abstractmethod
    def update_goal_runtime(self, new_goal) -> dict | None:
        pass

    @abstractmethod
    def end_session(self) -> str | None:
        pass

  # Adjust the URL based on where the FastAPI app is hosted

class AirisSession(AbstractAirisSession):
    def __init__(self, api_url):
        self.api_url = api_url
        self.session_id = None

    def initialize_session(self, goal, actions):
        """
        Initialize a session with available actions and get the session ID.
        """
        url = f"{self.api_url}/initialize"
        data = {"actions": actions,
                "goal": goal,
                }

        response = requests.post(url, json=data)
        if response.status_code == 200:
            response_data = response.json()
            self.session_id = response_data['session_id']
            print(f"Session Initialized: {self.session_id}")
            return self.session_id
        else:
            print(f"Error initializing session: {response.status_code}")
            return None

    def pre_action(self, environment_state):
        """
        Sends a request to the /api/preaction endpoint and returns
        the action, confidence, predicted_state, state_output, and edge_output.
        """
        url = f"{self.api_url}/preaction"
        data = {
            "session_id": self.session_id,
            "environment_state": environment_state
        }

        response = requests.post(url, json=data)
        if response.status_code == 200:
            response_data = response.json()
            return response_data['suggested_action'], response_data['state_output'], response_data['edges_output']

    def post_action(self, environment_state):
        """
        Send post-action request after an action is taken.
        """
        url = f"{self.api_url}/postaction"
        data = {
        'session_id': self.session_id,
        'environment_state': environment_state,
        }
        print(data['environment_state']['position'])

        response = requests.post(url, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error in post-action: {response.status_code}")
            print(f"{response.reason}")
            return None

    def update_goal_runtime(self, new_goal):
        """
        Update the goal during runtime.
        """
        url = f"{self.api_url}/runtime"
        data = {
            "session_id": self.session_id,
            "goal": new_goal
        }

        response = requests.post(url, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error updating goal: {response.status_code}")
            return None

    def end_session(self):
        """
        End the session and remove it from storage.
        """
        url = f"{self.api_url}/end"
        data = {"session_id": self.session_id}

        response = requests.post(url, json=data)
        if response.status_code == 200:
            return self.session_id
        else:
            print(f"Error ending session: {response.status_code}")
            return None


class EnvironmentState(Model):
    """
    Model representing the environment state, including agent's position and nearby grid information.
    """
    position: list
    nearby_grid: list

class InitializeRequest(Model):
    """
    Request model for initializing a session, which includes a goal and a list of actions.
    """
    goal: dict
    actions: List[str]
    session_id: Optional[str] = None

class InitializeResponse(Model):
    """
    Response model for session initialization. It returns the session ID, status, and a message.
    """
    session_id: str
    status: str
    message: str
    session_id_from_dump: Optional[str] = None

class PreActionRequest(Model):
    """
    Request model before an action is taken. It contains session ID and the environment state.
    """
    session_id: str
    environment_state: EnvironmentState
    session_id_from_dump: Optional[str] = None

class PreActionResponse(Model):
    """
    Response model after processing the pre-action phase.
    It returns the suggested action, confidence level, predicted state,
    state output, edge output, and applied rules.
    """
    suggested_action: str
    state_output: str
    edges_output: str

class PostActionRequest(Model):
    """
    Request model after an action has been performed.
    It includes both the suggested action and the actual action taken,
    as well as the predicted and actual states, state and edge outputs, and applied rules.
    """
    session_id: str
    environment_state: EnvironmentState


class PostActionResponse(Model):
    """
    Response model after processing the pre-action phase.
    It returns the suggested action, confidence level, predicted state,
    state output, edge output, and applied rules.
    """
    suggested_action: str | None = None
    state_output: str | None = None
    edges_output: str | None = None


class RuntimeRequest(Model):
    """
    Request model for updating the goal during runtime.
    """
    session_id: str
    goal: dict

class RuntimeResponse(Model):
    """
    Response model after updating the goal during runtime.
    It returns the updated status and message.
    """
    status: str
    message: str

class EndSessionRequest(Model):
    """
    Request model for ending a session. It only requires the session ID.
    """
    session_id: str

class EndSessionResponse(Model):
    """
    Response model after a session has been successfully ended.
    It returns the status and a confirmation message.
    """
    status: str
    message: str



class AgentAirisSession(AbstractAirisSession):
    def __init__(self, agent_address: str) -> None:
        self._identity: Identity = Identity.generate()
        self._agent_address: str = agent_address
        self._session_id: str | None = None

    @property
    def session_id(self) -> str:
        assert self._session_id is not None
        return self._session_id

    def initialize_session(self, goal: dict, actions: list[str]) -> str | None:
        response = self._send_and_receive(
            InitializeRequest(goal=goal, actions=actions),
            InitializeResponse
        )
        if response is None:
            print(f"Error initializing session")
            return None

        assert isinstance(response, InitializeResponse)
        self._session_id = response.session_id

        print(f"Session Initialized: {self.session_id}")
        return self.session_id


    def pre_action(self, environment_state: dict) -> tuple[str, str, str]:
        response = self._send_and_receive(
            PreActionRequest(
                session_id=self.session_id,
                environment_state=EnvironmentState.parse_obj(environment_state)
            ),
            PreActionResponse,
        )

        assert isinstance(response, PreActionResponse)
        return response.suggested_action, response.state_output, response.edges_output

    def post_action(self, environment_state) -> dict | None:
        response = self._send_and_receive(
            PostActionRequest(
                session_id=self.session_id,
                environment_state=EnvironmentState.parse_obj(environment_state),
            ),
            PostActionResponse,
        )
        if response is None:
            print(f"Error in post-action phase")
            return None

        assert isinstance(response, PostActionResponse)
        return response.dict(exclude_none=True)

    def update_goal_runtime(self, new_goal) -> dict | None:
        response = self._send_and_receive(
            RuntimeRequest(session_id=self.session_id, goal=new_goal),
            RuntimeResponse
        )
        if response is None:
            print(f"Error updating goal")
            return None

        assert isinstance(response, RuntimeResponse)
        return response.dict()

    def end_session(self) -> str | None:
        response = self._send_and_receive(
            EndSessionRequest(session_id=self.session_id),
            EndSessionResponse
        )
        if response is None:
            print(f"Error ending session")
            return None

        assert isinstance(response, EndSessionResponse)
        return self.session_id

    def _send_and_receive(self, request: Model, response_type: Type[Model]) -> Model | None:
        return asyncio.run(self._send_and_receive_inner(request, response_type))

    async def _send_and_receive_inner(self, request: Model, response_type: Type[Model]) -> Model | None:
        try:
            response = await asyncio.wait_for(
                send_sync_message(
                    self._agent_address,
                    request,
                    response_type=response_type,
                    sender=self._identity,
                ),
                timeout=5,
            )

            if isinstance(response, response_type):
                return response

            print('Unexpected response', response)

        except TimeoutError:
            print('Timedout waiting for response to', request)
            return None

        print('Fatal Error sending', request)
        return None
