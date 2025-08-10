from goalserve_client import OptimizedGoalServeClient

client = OptimizedGoalServeClient()
sports = client.get_available_sports()
print(f'Found {len(sports)} sports:')
for s in sports:
    print(f'- {s["name"]}: {s["event_count"]} events')
