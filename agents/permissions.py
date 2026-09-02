# ============================================================
# SHOP SENSE AI - PERMISSIONS
# ============================================================


def is_admin(role):
    """
    Return True when the current user is an ADMIN.
    """

    return str(role).strip().upper() == "ADMIN"


def is_staff(role):
    """
    Return True when the current user is STAFF.
    """

    return str(role).strip().upper() == "STAFF"


def can_access_admin_features(role):
    """
    Check whether the user can access
    administrator-only features.
    """

    return is_admin(role)


def can_create_sale(role):
    """
    Check whether the user can create sales.
    """

    return role in [
        "ADMIN",
        "STAFF"
    ]


def can_view_inventory(role):
    """
    Check whether the user can view inventory.
    """

    return role in [
        "ADMIN",
        "STAFF"
    ]


def can_use_ai(role):
    """
    Check whether the user can use
    the AI Sales Assistant.
    """

    return role in [
        "ADMIN",
        "STAFF"
    ]