import React, { useState, useEffect } from "react";
import { jwtDecode } from "jwt-decode";
import toastr from "toastr";
import "toastr/build/toastr.min.css";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min";

const mockProducts = [
  {
    id: 1,
    product_name: "Organic Honey",
    description: "Pure and raw honey from natural hives.",
    category: "Food",
    origin: "USA",
    price: 12.99,
    ingredients: "Honey",
  },
  {
    id: 2,
    product_name: "Almond Milk",
    description: "Unsweetened almond milk rich in calcium.",
    category: "Beverage",
    origin: "Canada",
    price: 3.49,
    ingredients: "Almonds, Water, Calcium carbonate",
  },
];

const ConsumerDashboard = () => {
  const token = localStorage.getItem("token");
  const [products, setProducts] = useState(mockProducts);
  const [cart, setCart] = useState([]);
  const [showModal, setShowModal] = useState(false);

  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    address: "",
  });

  useEffect(() => {
    try {
      const decoded = jwtDecode(token);
      if (decoded.role !== "consumer") {
        window.location.href = "/";
        return;
      }
      // fetchProducts();
    } catch {
      window.location.href = "/";
    }
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get("http://localhost:8000/products", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setProducts(response.data);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Failed to fetch products.";
      toastr.error(errorMsg);
    }
  };

  const addToCart = (product) => {
    setCart([...cart, product]);
  };

  const removeFromCart = (id) => {
    setCart(cart.filter((item) => item.id !== id));
  };

  const isInCart = (id) => cart.some((item) => item.id === id);

  const handleOpenModal = () => {
    if (cart.length === 0) {
      toastr.warning("Cart is empty.");
      return;
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
  };

  const handleFormChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleConfirmOrder = () => {
    if (!form.name || !form.email || !form.phone || !form.address) {
      toastr.error("Please fill all fields.");
      return;
    }

    // Simulate API call
    setTimeout(() => {
      console.log("Order placed with details:", form, "Cart:", cart);
      toastr.success("Order placed successfully!");
      setCart([]);
      setForm({ name: "", email: "", phone: "", address: "" });
      setShowModal(false);
    }, 800);
  };

  return (
    <div className="container">
      <h2 className="my-4">Consumer Dashboard</h2>
      <div className="table-responsive">
        <table className="table table-bordered table-hover">
          <thead className="table-light">
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Category</th>
              <th>Origin</th>
              <th>Price</th>
              <th>Ingredients</th>
              <th>Cart</th>
            </tr>
          </thead>
          <tbody>
            {products.length === 0 ? (
              <tr>
                <td colSpan="7" className="text-center">
                  Loading products...
                </td>
              </tr>
            ) : (
              products.map((p) => (
                <tr key={p.id}>
                  <td>{p.product_name}</td>
                  <td>{p.description}</td>
                  <td>{p.category}</td>
                  <td>{p.origin}</td>
                  <td>${p.price.toFixed(2)}</td>
                  <td style={{ whiteSpace: "pre-wrap" }}>{p.ingredients}</td>
                  <td>
                    {isInCart(p.id) ? (
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => removeFromCart(p.id)}
                      >
                        Remove
                      </button>
                    ) : (
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => addToCart(p)}
                      >
                        Add
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <button className="btn btn-success mt-3" onClick={handleOpenModal}>
        Buy Selected ({cart.length})
      </button>

      {/* Order Confirmation Modal */}
      {showModal && (
        <div className="modal show fade d-block" tabIndex="-1">
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Confirm Your Order</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={handleCloseModal}
                ></button>
              </div>
              <div className="modal-body">
                <form>
                  <div className="mb-2">
                    <label className="form-label">Full Name</label>
                    <input
                      type="text"
                      className="form-control"
                      name="name"
                      value={form.name}
                      onChange={handleFormChange}
                    />
                  </div>
                  <div className="mb-2">
                    <label className="form-label">Email</label>
                    <input
                      type="email"
                      className="form-control"
                      name="email"
                      value={form.email}
                      onChange={handleFormChange}
                    />
                  </div>
                  <div className="mb-2">
                    <label className="form-label">Phone Number</label>
                    <input
                      type="text"
                      className="form-control"
                      name="phone"
                      value={form.phone}
                      onChange={handleFormChange}
                    />
                  </div>
                  <div className="mb-2">
                    <label className="form-label">Delivery Address</label>
                    <textarea
                      className="form-control"
                      name="address"
                      rows="3"
                      value={form.address}
                      onChange={handleFormChange}
                    ></textarea>
                  </div>
                </form>
              </div>
              <div className="modal-footer">
                <button
                  className="btn btn-secondary"
                  onClick={handleCloseModal}
                >
                  Cancel
                </button>
                <button className="btn btn-primary" onClick={handleConfirmOrder}>
                  Confirm Order
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConsumerDashboard;