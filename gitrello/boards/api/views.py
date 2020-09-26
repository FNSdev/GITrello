from rest_framework import views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authentication.services import PermissionsService
from boards.api.serializers import CreateBoardSerializer, CreateBoardMembershipSerializer, GetBoardPermissionsSerializer
from boards.services import BoardService, BoardMembershipService
from gitrello.exceptions import APIRequestValidationException, PermissionDeniedException


class BoardsView(views.APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        serializer = CreateBoardSerializer(data=request.data)
        if not serializer.is_valid():
            raise APIRequestValidationException(serializer_errors=serializer.errors)

        service = BoardService()
        if not service.can_create_board(
                user_id=request.user.id,
                organization_id=serializer.validated_data['organization_id']):
            raise PermissionDeniedException

        board = service.create_board(**serializer.validated_data)
        return Response(
            status=201,
            data={
                'id': str(board.id),
                'name': board.name,
            },
        )


class BoardMembershipsView(views.APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        serializer = CreateBoardMembershipSerializer(data=request.data)
        if not serializer.is_valid():
            raise APIRequestValidationException(serializer_errors=serializer.errors)

        service = BoardMembershipService()
        if not service.can_add_member(user_id=request.user.id, **serializer.validated_data):
            raise PermissionDeniedException

        board_membership = service.add_member(**serializer.validated_data)
        return Response(
            status=201,
            data={
                'id': str(board_membership.id),
            },
        )


class BoardMembershipView(views.APIView):
    permission_classes = (IsAuthenticated, )

    def delete(self, request, *args, **kwargs):
        service = BoardMembershipService()
        if not service.can_delete_member(user_id=request.user.id, board_membership_id=kwargs['id']):
            raise PermissionDeniedException

        service.delete_member(board_membership_id=kwargs['id'])
        return Response(status=204)


class BoardPermissionsView(views.APIView):
    def get(self, request, *args, **kwargs):
        serializer = GetBoardPermissionsSerializer(data=request.data)
        if not serializer.is_valid():
            raise APIRequestValidationException(serializer_errors=serializer.errors)

        permissions = PermissionsService.get_board_permissions(**serializer.validated_data)
        return Response(status=200, data=permissions.to_json())
