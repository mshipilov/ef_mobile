import bcrypt

def encrypt_pass(pass_str):
    pass_encoded = pass_str.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_pass = bcrypt.hashpw(pass_encoded, salt)
    return hashed_pass

def check_encrypred_pass(pass_str, hashed_pass):
    return bcrypt.checkpw(pass_str, hashed_pass)

