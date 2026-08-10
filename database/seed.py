# database/seed.py
from models import db, Vehicle

def seed_vehicles():
    """Seed vehicle data if empty"""
    if Vehicle.query.count() == 0:
        vehicles = [
            {
                'name': 'Ferrari',
                'brand': 'Ferrari',
                'image': 'ferrari.jpg',
                'rental_price': 10000.00,
                'daily_earning': 500.00,
                'rental_period': 30,
                'sort_order': 1,
                'is_active': True,
                'is_available': True,
                'description': 'Luxury Italian sports car with exceptional performance.'
            },
            {
                'name': 'Porsche',
                'brand': 'Porsche',
                'image': 'porsche.jpg',
                'rental_price': 8000.00,
                'daily_earning': 400.00,
                'rental_period': 30,
                'sort_order': 2,
                'is_active': True,
                'is_available': True,
                'description': 'German engineering excellence with precision handling.'
            },
            {
                'name': 'Jaguar',
                'brand': 'Jaguar',
                'image': 'jaguar.jpg',
                'rental_price': 7000.00,
                'daily_earning': 350.00,
                'rental_period': 30,
                'sort_order': 3,
                'is_active': True,
                'is_available': True,
                'description': 'British luxury and elegance with powerful performance.'
            },
            {
                'name': 'Mercedes-Benz',
                'brand': 'Mercedes-Benz',
                'image': 'mercedes.jpg',
                'rental_price': 5500.00,
                'daily_earning': 290.00,
                'rental_period': 30,
                'sort_order': 4,
                'is_active': True,
                'is_available': True,
                'description': 'Premium German luxury sedan with cutting-edge technology.'
            },
            {
                'name': 'BMW',
                'brand': 'BMW',
                'image': 'bmw.jpg',
                'rental_price': 4000.00,
                'daily_earning': 230.00,
                'rental_period': 30,
                'sort_order': 5,
                'is_active': True,
                'is_available': True,
                'description': 'The ultimate driving machine with sporty performance.'
            },
            {
                'name': 'Isuzu',
                'brand': 'Isuzu',
                'image': 'isuzu.jpg',
                'rental_price': 3500.00,
                'daily_earning': 200.00,
                'rental_period': 30,
                'sort_order': 6,
                'is_active': True,
                'is_available': True,
                'description': 'Reliable and durable SUV perfect for any terrain.'
            },
            {
                'name': 'Mazda',
                'brand': 'Mazda',
                'image': 'mazda.jpg',
                'rental_price': 3000.00,
                'daily_earning': 170.00,
                'rental_period': 30,
                'sort_order': 7,
                'is_active': True,
                'is_available': True,
                'description': 'Japanese reliability with sporty design and efficiency.'
            },
            {
                'name': 'Toyota',
                'brand': 'Toyota',
                'image': 'toyota.jpg',
                'rental_price': 2500.00,
                'daily_earning': 150.00,
                'rental_period': 30,
                'sort_order': 8,
                'is_active': True,
                'is_available': True,
                'description': 'World-class reliability, efficiency, and value for money.'
            }
        ]
        
        for v in vehicles:
            vehicle = Vehicle(**v)
            db.session.add(vehicle)
        db.session.commit()
        print(f"✅ {len(vehicles)} vehicles seeded successfully!")
        return True
    else:
        print(f"✅ Vehicles already exist ({Vehicle.query.count()} vehicles)")
        return False

def seed_database():
    """Seed all database tables"""
    seed_vehicles()