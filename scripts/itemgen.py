#!/usr/bin/env python
#made by alex elkabbany - 
from app import app, db, Item  # Import your app and Item model
import random

with app.app_context():
    # List of sample items
    items = [
        {"name": "Propress", "item_type": "Tool"},
        {"name": "Type B", "item_type": "Type B"},
        {"name": "Item 3", "item_type": "Type A"},
        {"name": "Pipe Wrench", "item_type": "Tool"},
        {"name": "Adjustable Wrench", "item_type": "Tool"},
        {"name": "Pliers", "item_type": "Tool"},
        {"name": "Pipe Cutter", "item_type": "Tool"},
        {"name": "Hacksaw", "item_type": "Tool"},
        {"name": "Plumber's Tape (Teflon Tape)", "item_type": "Tool"},
        {"name": "Plumber's Putty", "item_type": "Tool"},
        {"name": "Plunger", "item_type": "Tool"},
        {"name": "Toilet Auger (Closet Auger)", "item_type": "Tool"},
        {"name": "Drain Snake (Handheld or Electric)", "item_type": "Tool"},
        {"name": "Basin Wrench", "item_type": "Tool"},
        {"name": "Compression Sleeve Puller", "item_type": "Tool"},
        {"name": "Flaring Tool", "item_type": "Tool"},
        {"name": "Deburring Tool", "item_type": "Tool"},
        {"name": "Faucet Seat Wrench", "item_type": "Tool"},
        {"name": "Faucet Valve Seat Grinder", "item_type": "Tool"},
        {"name": "Propane Torch", "item_type": "Tool"},
        {"name": "Pipe Insulation Cutters", "item_type": "Tool"},
        {"name": "Pressure Gauge", "item_type": "Tool"},
    ]

    for item in items:
        # Create new Item object
        new_item = Item(
            name=item["name"],
            item_type=item["item_type"],
            group_id=random.randint(1, 5)  # Randomly assign a group_id between 1 and 5
        )

        # Add the new item to the session
        db.session.add(new_item)

    # Commit the session to save the new items
    db.session.commit()
