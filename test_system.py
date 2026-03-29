from backend.data_fetch import get_stock_data
from backend.signal_engine import generate_signal

data = get_stock_data("RELIANCE.NS")
result = generate_signal(data)

print("=== SIGNAL RESULT ===")
print(result)