# database/seed.py
from models import db, Vehicle

def seed_vehicles():
    """Seed vehicle data if empty"""
    if Vehicle.query.count() == 0:
        vehicles = [
            {'name': 'Ferrari', 'brand': 'Ferrari', 'rental_price': 10000, 'daily_earning': 500, 'rental_period': 30, 'sort_order': 1, 'is_active': True, 'is_available': True},
            {'name': 'Porsche', 'brand': 'Porsche', 'rental_price': 8000, 'daily_earning': 400, 'rental_period': 30, 'sort_order': 2, 'is_active': True, 'is_available': True},
            {'name': 'Jaguar', 'brand': 'Jaguar', 'rental_price': 7000, 'daily_earning': 350, 'rental_period': 30, 'sort_order': 3, 'is_active': True, 'is_available': True},
            {'name': 'Mercedes-Benz', 'brand': 'Mercedes-Benz', 'rental_price': 5500, 'daily_earning': 290, 'rental_period': 30, 'sort_order': 4, 'is_active': True, 'is_available': True},
            {'name': 'BMW', 'brand': 'BMW', 'rental_price': 4000, 'daily_earning': 230, 'rental_period': 30, 'sort_order': 5, 'is_active': True, 'is_available': True},
            {'name': 'Isuzu', 'brand': 'Isuzu', 'rental_price': 3500, 'daily_earning': 200, 'rental_period': 30, 'sort_order': 6, 'is_active': True, 'is_available': True},
            {'name': 'Mazda', 'brand': 'Mazda', 'rental_price': 3000, 'daily_earning': 170, 'rental_period': 30, 'sort_order': 7, 'is_active': True, 'is_available': True},
            {'name': 'Toyota', 'brand': 'Toyota', 'rental_price': 2500, 'daily_earning': 150, 'rental_period': 30, 'sort_order': 8, 'is_active': True, 'is_available': True}
        ]
        
        for v in vehicles:
            vehicle = Vehicle(**v)
            db.session.add(vehicle)
        db.session.commit()
        return True
    return False

def seed_database():
    """Seed all database tables"""
    seed_vehicles()