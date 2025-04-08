
def permisson_genarator(module_name):
    return [
        {"codename": f"view_{module_name.lower()}", "name":
         f"Can view{module_name.lower()}", "module": module_name},
        {"codename": f"add_{module_name.lower()}", "name":
         f"Can add {module_name.lower()}", "module": module_name},
        {"codename": f"edit_{module_name.lower()}", "name":
         f"Can edit {module_name.lower()}", "module": module_name},
        {"codename": f"delete_{module_name.lower()}", "name":
         f"Can delete {module_name.lower()}", "module": module_name},
    ]

