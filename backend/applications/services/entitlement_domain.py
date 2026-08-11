class EntitlementService:
    AUTO_APPLY_SERVER = 'AUTO_APPLY_SERVER'
    
    @classmethod
    def has_entitlement(cls, user, entitlement_name: str) -> bool:
        """
        Determines if the given user has access to the specified product feature.
        In Phase 5F, we default to True for local development/testing.
        In production, this would query a billing/subscription provider model.
        """
        if entitlement_name == cls.AUTO_APPLY_SERVER:
            # For Phase 5F, all test users have this entitlement
            return True
            
        return False
