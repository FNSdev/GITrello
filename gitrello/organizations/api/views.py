from rest_framework import views
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from gitrello.exceptions import APIRequestValidationException, PermissionDeniedException
from organizations.api.serializers import (
    CreateOrganizationSerializer, CreateOrganizationInviteSerializer, UpdateOrganizationInviteSerializer,
)
from organizations.services import OrganizationService, OrganizationInviteService, OrganizationMembershipService


class OrganizationsView(views.APIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (SessionAuthentication, TokenAuthentication)

    def post(self, request, *args, **kwargs):
        serializer = CreateOrganizationSerializer(data=request.data)
        if not serializer.is_valid():
            raise APIRequestValidationException(serializer_errors=serializer.errors)

        organization = OrganizationService().create_organization(owner_id=request.user.id, **serializer.validated_data)
        return Response(
            status=201,
            data={
                'id': str(organization.id),
                'name': organization.name,
            },
        )


class OrganizationInvitesView(views.APIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (SessionAuthentication, TokenAuthentication)

    def post(self, request, *args, **kwargs):
        serializer = CreateOrganizationInviteSerializer(data=request.data)
        if not serializer.is_valid():
            raise APIRequestValidationException(serializer_errors=serializer.errors)

        service = OrganizationInviteService()
        if not service.can_send_invite(
                user_id=request.user.id,
                organization_id=serializer.validated_data['organization_id']):
            raise PermissionDeniedException

        invite = service.send_invite(**serializer.validated_data)
        return Response(
            status=201,
            data={
                'id': str(invite.id),
                'status': invite.get_status_display(),
            },
        )


class OrganizationInviteView(views.APIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (SessionAuthentication, TokenAuthentication)

    def patch(self, request, *args, **kwargs):
        serializer = UpdateOrganizationInviteSerializer(data=request.data)
        if not serializer.is_valid():
            raise APIRequestValidationException(serializer_errors=serializer.errors)

        service = OrganizationInviteService()
        if not service.can_update_invite(user_id=request.user.id, organization_invite_id=kwargs['id']):
            raise PermissionDeniedException

        invite = service.update_invite(
            organization_invite_id=kwargs['id'],
            **serializer.validated_data,
        )
        return Response(
            status=200,
            data={
                'id': str(invite.id),
                'status': invite.get_status_display(),
            },
        )


class OrganizationMembershipView(views.APIView):
    permission_classes = (IsAuthenticated, )
    authentication_classes = (SessionAuthentication, TokenAuthentication)

    def delete(self, request, *args, **kwargs):
        service = OrganizationMembershipService()
        if not service.can_delete_member(user_id=request.user.id, organization_membership_id=kwargs['id']):
            raise PermissionDeniedException

        service.delete_member(organization_membership_id=kwargs['id'])
        return Response(status=204)
