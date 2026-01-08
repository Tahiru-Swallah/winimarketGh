def resolve_recipient(order, role):
    try:
        if role == "buyer" and order.buyer and order.buyer.user:
            return [{
                "email": order.buyer.user.email,
                "user_id": order.buyer.user.id,
            }]

        if role == "seller" and order.seller and order.seller.profile:
            user = order.seller.profile.user
            return [{
                "email": user.email,
                "user_id": user.id,
            }]
    except AttributeError:
        pass

    return []
