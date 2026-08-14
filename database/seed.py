# database/seed.py
from models import db, Vehicle

def seed_vehicles():
    """Seed vehicle data if empty"""
    if Vehicle.query.count() == 0:
        vehicles = [
            {
                'name': 'Toyota',
                'brand': 'Toyota',
                'image': 'toyota.jpg',
                'rental_price': 2500.00,
                'daily_earning': 100.00,
                'rental_period': 60,
                'sort_order': 8,
                'is_active': True,
                'is_available': True,
                'description': 'World-class reliability, efficiency, and value for money.'
            },
            {
                'name': 'Mazda',
                'brand': 'Mazda',
                'image': 'mazda.jpg',
                'rental_price': 4800.00,
                'daily_earning': 180.00,
                'rental_period': 90,
                'sort_order': 7,
                'is_active': True,
                'is_available': True,
                'description': 'Japanese reliability with sporty design and efficiency.'
            },
            {
                'name': 'Isuzu',
                'brand': 'Isuzu',
                'image': 'isuzu.jpg',
                'rental_price': 6800.00,
                'daily_earning': 250.00,
                'rental_period': 120,
                'sort_order': 6,
                'is_active': True,
                'is_available': True,
                'description': 'Reliable and durable SUV perfect for any terrain.'
            },
            {
                'name': 'BMW',
                'brand': 'BMW',
                'image': 'bmw.jpg',
                'rental_price': 9000.00,
                'daily_earning': 270.00,
                'rental_period': 150,
                'sort_order': 5,
                'is_active': True,
                'is_available': True,
                'description': 'The ultimate driving machine with sporty performance.'
            },
            {
                'name': 'Mercedes-Benz',
                'brand': 'Mercedes-Benz',
                'image': 'mercedes.jpg',
                'rental_price': 12000.00,
                'daily_earning': 320.00,
                'rental_period': 170,
                'sort_order': 4,
                'is_active': True,
                'is_available': True,
                'description': 'Premium German luxury sedan with cutting-edge technology.'
            },
            {
                'name': 'Jaguar',
                'brand': 'Jaguar',
                'image': 'jaguar.jpg',
                'rental_price': 15000.00,
                'daily_earning': 450.00,
                'rental_period': 180,
                'sort_order': 3,
                'is_active': True,
                'is_available': True,
                'description': 'British luxury and elegance with powerful performance.'
            },
            {
                'name': 'Porsche',
                'brand': 'Porsche',
                'image': 'porsche.jpg',
                'rental_price': 18000.00,
                'daily_earning': 500.00,
                'rental_period': 190,
                'sort_order': 2,
                'is_active': True,
                'is_available': True,
                'description': 'German engineering excellence with precision handling.'
            },
            {
                'name': 'Ferrari',
                'brand': 'Ferrari',
                'image': 'ferrari.jpg',
                'rental_price': 22000.00,
                'daily_earning': 700.00,
                'rental_period': 200,
                'sort_order': 1,
                'is_active': True,
                'is_available': True,
                'description': 'Luxury Italian sports car with exceptional performance.'
            }
        ]
        
        for v in vehicles:
            vehicle = Vehicle(**v)
            db.session.add(vehicle)
        db.session.commit()
        print(f"✅ {len(vehicles)} vehicles seeded successfully with new pricing!")
        return True
    else:
        print(f"✅ Vehicles already exist ({Vehicle.query.count()} vehicles)")
        return False

def update_vehicle_pricing():
    """Update existing vehicles with new pricing"""
    vehicles_data = [
        {'name': 'Toyota', 'rental_price': 2500, 'daily_earning': 100, 'rental_period': 60, 'sort_order': 8},
        {'name': 'Mazda', 'rental_price': 4800, 'daily_earning': 180, 'rental_period': 90, 'sort_order': 7},
        {'name': 'Isuzu', 'rental_price': 6800, 'daily_earning': 250, 'rental_period': 120, 'sort_order': 6},
        {'name': 'BMW', 'rental_price': 9000, 'daily_earning': 270, 'rental_period': 150, 'sort_order': 5},
        {'name': 'Mercedes-Benz', 'rental_price': 12000, 'daily_earning': 320, 'rental_period': 170, 'sort_order': 4},
        {'name': 'Jaguar', 'rental_price': 15000, 'daily_earning': 450, 'rental_period': 180, 'sort_order': 3},
        {'name': 'Porsche', 'rental_price': 18000, 'daily_earning': 500, 'rental_period': 190, 'sort_order': 2},
        {'name': 'Ferrari', 'rental_price': 22000, 'daily_earning': 700, 'rental_period': 200, 'sort_order': 1}
    ]
    
    updated = 0
    for data in vehicles_data:
        vehicle = Vehicle.query.filter_by(name=data['name']).first()
        if vehicle:
            vehicle.rental_price = data['rental_price']
            vehicle.daily_earning = data['daily_earning']
            vehicle.rental_period = data['rental_period']
            vehicle.sort_order = data['sort_order']
            vehicle.total_profit = (data['daily_earning'] * data['rental_period']) - data['rental_price']
            vehicle.is_active = True
            vehicle.is_available = True
            updated += 1
            print(f"✅ Updated {data['name']}: Price={data['rental_price']}, Daily={data['daily_earning']}, Days={data['rental_period']}")
    
    if updated > 0:
        db.session.commit()
        print(f"✅ {updated} vehicles updated successfully with new pricing!")
    else:
        print("ℹ️ No vehicles found to update")
    
    return updated

def seed_database():
    """Seed all database tables"""
    # Check if vehicles exist
    count = Vehicle.query.count()
    if count == 0:
        seed_vehicles()
    else:
        print(f"ℹ️ Vehicles already exist ({count} vehicles)")
        # Update existing vehicles with new pricing
        print("🔄 Updating existing vehicles with new pricing...")
        update_vehicle_pricing()