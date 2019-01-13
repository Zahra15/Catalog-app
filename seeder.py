from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Item, User
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Create dummy user
User1 = User(name="User 1", email="user@user.com",
             picture='')
session.add(User1)
session.commit()

# category Headphones
category1 = Category(title="Headphones")

session.add(category1)
session.commit()

Item1 = Item(title="Bitzen", description=""""Wireless active noise cancelling headphones
 - bluetooth over ear headphones
  - portable stereo earphones for women men""", category=category1, user_id=1)

session.add(Item1)
session.commit()

Item2 = Item(title="Sennheiser", description="""Sennheiser
 HD 600  Open back professional headphone""", category=category1, user_id=1)

session.add(Item2)
session.commit()

Item3 = Item(title="beyerdynamic", description="""The DT 1990 PRO
 reference headphones combine these decades
  of expertise in headphone technology
  with the latest Tesla driver technology
   and an open design.""", category=category1, user_id=1)

session.add(Item3)
session.commit()

Item4 = Item(title="Audio-Technica", description="""Audio-Technica
 ATH-M50x Professional Monitor Headphones
  + Slappa Full Sized HardBody
   PRO Headphone Case (SL-HP-07)""", category=category1, user_id=1)

session.add(Item4)
session.commit()


# category Smartwatches
category2 = Category(title="Smartwatches")

session.add(category2)
session.commit()

Item1 = Item(title="Samsung Galaxy Watch", description="""Live a stronger
, smarter life with Galaxy
 Watch at your wrist Rest well and
  stay active with built-in health tracking and
  a Bluetooth connection that keeps everything at your wrist Plus,
  go for days without charging""", category=category2, user_id=1)

session.add(Item1)
session.commit()

Item2 = Item(title="Fitbit", description="""Start dynamic personalized workouts
 on your wrist with step-by-step coaching. Syncing range:
  Up to 30 feet. Certain features like smartphone
   notifications may require Android 5.0+. Syncs
    with Mac OS X 10.6 and up, iPhone 4S and later
    , iPad 3 gen.
     and later
    , Android 4.4 and later
     and Windows 10 devices""", category=category2, user_id=1)

session.add(Item2)
session.commit()

Item3 = Item(title="Amazfit", description="""Look as Good as You Feel:
 With a range of colors and options, the Bip is designed to be worn
  as an extension of your personal style. Weighing only 1.1oz (32g)
  , and with a bright
  , transflective always-on 1.28""", category=category2, user_id=1)

session.add(Item3)
session.commit()


print "added catalog items!"
