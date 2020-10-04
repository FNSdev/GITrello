import logging

from django.db.transaction import atomic
from django.views.generic import RedirectView
from rest_framework import views
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authentication.api.serializers import CreateUserSerializer, CreateOauthStateSerializer
from authentication.services import GithubOauthService, OauthStateService, UserService
from github_integration import GithubIntegrationServiceAPIClient
from gitrello.exceptions import APIRequestValidationException, HttpRequestException
from gitrello.handlers import retry_on_transaction_serialization_error

logger = logging.getLogger(__name__)


class UsersView(views.APIView):
    @retry_on_transaction_serialization_error
    @atomic
    def post(self, request, *args, **kwargs):
        serializer = CreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            raise APIRequestValidationException(serializer_errors=serializer.errors)

        user = UserService.create_user(**serializer.validated_data)
        return Response(
            status=201,
            data={
                'id': str(user.id),
                'token': UserService.get_jwt_token(user.id),
            },
        )


class AuthTokenView(views.APIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (BasicAuthentication, )

    def get(self, request, *args, **kwargs):
        return Response(
            status=200,
            data={
                'token': UserService().get_jwt_token(request.user.id),
                'user': {
                    'id': str(request.user.id),
                    'username': request.user.username,
                    'email': request.user.email,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                },
            },
        )


class AuthTokenOwnerView(views.APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        return Response(
            status=200,
            data={
                'id': str(request.user.id),
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'username': request.user.username,
            },
        )


class GithubOauthView(RedirectView):
    url = '/profile'

    # TODO add tests
    @retry_on_transaction_serialization_error
    @atomic
    def get(self, request, *args, **kwargs):
        error = request.GET.get('error')
        if error:
            # TODO show error message to user somehow
            return super().get(request, *args, **kwargs)

        code = request.GET.get('code')
        state = request.GET.get('state')

        if not code or not state:
            # TODO show error message to user somehow
            return super().get(request, *args, **kwargs)

        token = GithubOauthService.exchange_code_for_token(code)

        oauth_state = OauthStateService.get_by_state(state)
        user_id = oauth_state.user_id

        OauthStateService.delete(oauth_state.id)

        # TODO show error message to user somehow
        try:
            github_integration_service_api_client = GithubIntegrationServiceAPIClient(user_id)
            github_integration_service_api_client.create_github_profile(token)
        except HttpRequestException as e:
            logger.exception(e)

        return super().get(request, *args, **kwargs)


class OauthStatesView(views.APIView):
    permission_classes = (IsAuthenticated, )

    # TODO add tests
    @retry_on_transaction_serialization_error
    @atomic
    def post(self, request, *args, **kwargs):
        serializer = CreateOauthStateSerializer(data=request.data)
        if not serializer.is_valid():
            raise APIRequestValidationException(serializer_errors=serializer.errors)

        oauth_state = OauthStateService.get_or_create(user_id=request.user.id, **serializer.validated_data)
        return Response(
            status=201,
            data={
                'id': str(oauth_state.id),
                'user_id': oauth_state.user_id,
                'provider': oauth_state.provider,
                'state': oauth_state.state,
            },
        )
