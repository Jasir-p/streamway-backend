import random
import string

def generate_password(length=8):
    # Define the characters to choose from
    characters = string.ascii_letters + string.digits
    
   
    password = ''.join(random.choice(characters) for i in range(length))
    print(password)
    
    return password




