class PluginServiceLocator:
    """Central access point for optional plugin utilities."""

    @staticmethod
    def get_unicode_handler():
        """Return the unified Unicode handler module."""
        import unicode_handler

        return unicode_handler
