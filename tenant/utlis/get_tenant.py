
def get_schema_name(request):
    """Get the schema name from the request."""
    tenant = request.tenant
    return tenant.schema_name