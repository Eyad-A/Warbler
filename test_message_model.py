"""Message Model Tests"""

from unittest import TestCase 
from sqlalchemy import exc 
from models import db, User, Message, Follows, Likes 
import os 

os.environ['DATABASE_URL'] = "postgresql:///warbler-test" 

from app import app 

db.create_all()  

class UserModelTestCase(TestCase):
    """Tests for messages"""

    def setUp(self): 
        """Create the test client and add data"""
        db.drop_all()
        db.create_all()

        self.uid = 1234 
        u = User.signup("test", "test@gmail.com", "password", None) 
        u.id = self.uid 
        db.session.commit() 

        self.u = User.query.get(self.uid) 
        self.client = app.test_client() 
    
    def tearDown(self): 
        response = super().tearDown()
        db.session.rollback()
        return response 

    def test_message_model(self):
        """Message model test"""

        message = Message(text="Example message", user_id=self.uid)
        
        db.session.add(message) 
        db.session.commit() 

        #Check if the user has a message 
        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, "Example message")

    def test_message_like(self):
        message1 = Message(text="message 1", user_id=self.uid)
        message2 = Message(text="message 2", user_id=self.uid)

        u = User.signup("testing", "testing@mycompany.com", "password", None)        
        uid = 456
        u.id = uid  

        db.session.add_all([message1, message2, u])
        db.session.commit()

        u.likes.append(message1)
        db.session.commit() 

        like = Likes.query.filter(Likes.user_id == uid).all() 
        self.assertEqual(len(like), 1)
        self.assertEqual(like[0].message_id, message1.id) 



        