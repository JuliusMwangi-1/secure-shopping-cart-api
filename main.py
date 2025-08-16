from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import json
import os

app = FastAPI(title="Secure Shopping Cart API")
security = HTTPBasic()

USERS_FILE = "users.json"
PRODUCTS_FILE = "products.json"
CART_FILE = "cart.json"

# ---------- Helper Functions ----------
def load_json(file):
    if not os.path.exists(file):
        return {}
    try:
        with open(file, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Error decoding {file}")
    except Exception:
        raise HTTPException(status_code=500, detail=f"Error reading {file}")

def save_json(file, data):
    try:
        with open(file, "w") as f:
            json.dump(data, f, indent=4)
    except Exception:
        raise HTTPException(status_code=500, detail=f"Error writing to {file}")

def authenticate(credentials: HTTPBasicCredentials):
    users = load_json(USERS_FILE)
    if credentials.username not in users or users[credentials.username]["password"] != credentials.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return users[credentials.username]

def admin_required(user: dict = Depends(authenticate)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user

# ---------- Routes ----------
@app.post("/admin/add_product/")
def add_product(name: str, price: float, user: dict = Depends(admin_required)):
    try:
        products = load_json(PRODUCTS_FILE)
        if name in products:
            raise HTTPException(status_code=400, detail="Product already exists")
        products[name] = {"price": price}
        save_json(PRODUCTS_FILE, products)
        return {"message": f"Product {name} added successfully"}
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error while adding product")

@app.get("/products/")
def get_products():
    try:
        products = load_json(PRODUCTS_FILE)
        return products
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to fetch products")

@app.post("/cart/add/")
def add_to_cart(product_name: str, user: dict = Depends(authenticate)):
    try:
        products = load_json(PRODUCTS_FILE)
        if product_name not in products:
            raise HTTPException(status_code=404, detail="Product not found")
        cart = load_json(CART_FILE)
        username = user["username"]
        if username not in cart:
            cart[username] = []
        cart[username].append(product_name)
        save_json(CART_FILE, cart)
        return {"message": f"{product_name} added to {username}'s cart"}
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error while adding to cart")
