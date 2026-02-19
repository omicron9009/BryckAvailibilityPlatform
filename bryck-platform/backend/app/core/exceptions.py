from fastapi import HTTPException, status


class MachineNotFoundError(HTTPException):
    def __init__(self, machine_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine '{machine_id}' not found.",
        )


class MachineIPConflictError(HTTPException):
    def __init__(self, ip: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A machine with IP '{ip}' already exists.",
        )


class MachineAlreadyDecommissionedError(HTTPException):
    def __init__(self, machine_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Machine '{machine_id}' is already decommissioned.",
        )


class BryckAPIUnavailableError(HTTPException):
    def __init__(self, detail: str = "BryckAPI is unreachable."):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
