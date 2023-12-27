from src import Auth


def test_authenticate():
    """Test for authenticate method"""
    auth = Auth.Auth()
    assert auth.authenticate("test", "test") == True
    assert auth.authenticate("test", "test2") == False
    assert auth.authenticate("test2", "test") == False
    assert auth.authenticate("test2", "test2") == False

def test_isUserExist():
    """Test for __isUserExist method"""
    auth = Auth.Auth()
    assert auth._Auth__isUserExist("test") == True
    assert auth._Auth__isUserExist("test2") == False

def test_isPasswordCorrect():
    """Test for __isPasswordCorrect method"""
    auth = Auth.Auth()
    assert auth._Auth__isPasswordCorrect("test", "test") == True
    assert auth._Auth__isPasswordCorrect("test", "test2") == False
    assert auth._Auth__isPasswordCorrect("test2", "test") == False
    assert auth._Auth__isPasswordCorrect("test2", "test2") == False
