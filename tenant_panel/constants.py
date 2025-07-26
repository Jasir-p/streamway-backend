

EMAIL_REGEX = r"^[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
CONTACT_REGEX = r"^(?!0{10})[0-9]{10}$"
NAME_REGEX = r"^(?=.*[A-Za-z])[A-Za-z0-9\s&.,'-]+$"
FORBIDDEN_TITLE_CHARS_REGEX =r"[\/\-_]"
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$'
NOTES_START_REGEX = r'^[A-Za-z0-9]'
NOTES_HAS_ALPHANUMERIC_REGEX = r'[A-Za-z0-9]'
CUSTOM_FIELD_NAME_REGEX = r'^[A-Za-z][A-Za-z0-9\s_-]*$'
CUSTOM_FIELD_VALUE_REGEX = r"^[A-Za-z0-9\s.,@!#$%&*()_+\-=\"']+$"
REPEATED_CHARACTER_PATTERN = r'^([A-Za-z0-9\s_-])\1+$'

