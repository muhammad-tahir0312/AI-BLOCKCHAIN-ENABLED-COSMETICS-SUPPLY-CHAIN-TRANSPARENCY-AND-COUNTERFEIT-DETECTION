import React, { useState, useEffect } from "react";
import axios from "axios";
import toastr from "toastr";
import "toastr/build/toastr.min.css";
import { jwtDecode } from "jwt-decode";
import { Modal, Button, Form } from "react-bootstrap";

const ConsumerDashboard = () => {
  const token = localStorage.getItem("token");
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [balance, setBalance] = useState(null);
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
      fetchProducts();
      // fetchUserBalance(); 
    } catch {
      window.location.href = "/";
    }
  }, [token]);

  // const fetchUserBalance = async () => {
  //   try {
  //     const response = await axios.get(`http://localhost:8000/user/${jwtDecode(token).exp}/balance`, {
  //       headers: {
  //         Authorization: `Bearer ${token}`,
  //       },
  //     });
  //     setBalance(response.data.total_balance); // Assuming 'total_balance' is the field in BalanceOut schema
  //   } catch (err) {
  //     const errorMsg = err.response?.data?.detail || "Failed to fetch balance.";
  //     toastr.error(errorMsg);
  //   }
  // };

  const fetchProducts = async () => {
    try {
      const response = await axios.get("http://localhost:8000/products", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setProducts(response.data);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Failed to load products.";
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
      toastr.warning("Your cart is empty.");
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

  // const handleConfirmOrder = async () => {
  //   if (!form.name || !form.email || !form.phone || !form.address) {
  //     toastr.error("Please fill in all required fields.");
  //     return;
  //   }

  //   const orderData = {
  //     consumer_id: jwtDecode(token).exp,
  //     product_id: cart.id,
  //     total_amount: cart.reduce((sum, p) => sum + p.price, 0),
  //     delivery_address: form.address,
  //     customer_name: form.name,
  //     email: form.email,
  //     contact_number: form.phone,
  //   };

  //   try {
  //     const response = await axios.post("http://localhost:8000/orders", orderData, {
  //       headers: {
  //         Authorization: `Bearer ${token}`,
  //         "Content-Type": "application/json",
  //       },
  //     });

  //     toastr.success("Order placed successfully!");
  //     setCart([]);
  //     setForm({ name: "", email: "", phone: "", address: "" });
  //     setShowModal(false);
  //     console.log("Order Response:", response.data);
  //   } catch (error) {
  //     const errorMsg = error.response?.data?.detail || "Failed to place order.";
  //     toastr.error(errorMsg);
  //   }
  // };
  const handleConfirmOrder = async () => {
    if (!form.name || !form.email || !form.phone || !form.address) {
      toastr.error("Please fill in all required fields.");
      return;
    }
  
    const orderData = {
      consumer_id: jwtDecode(token).exp, // Assuming exp as consumer_id
      product_id: cart.map((item) => item.id), // Send an array of product IDs
      total_amount: cart.reduce((sum, p) => sum + p.price, 0),
      delivery_address: form.address,
      customer_name: form.name,
      email: form.email,
      contact_number: form.phone,
    };
  
    try {
      // Step 1: Create the order
      const orderResponse = await axios.post("http://localhost:8000/orders", orderData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
  
      toastr.success("Order placed successfully!");
  
      // Step 2: Create the payment after order creation
      const paymentData = {
        amount: cart.reduce((sum, p) => sum + p.price, 0), // Payment amount is the total price
        order_id: orderResponse.data.id,
      };
  
      // Assuming orderResponse.data contains the created order's ID
      await axios.post(`http://localhost:8000/orders/${orderResponse.data.id}/payment`, paymentData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
  
    // Step 3: Fetch the payment amount after creating the payment
    fetchPaymentAmount(orderResponse.data.id);

    setCart([]); // Clear the cart after order and payment creation
    setForm({ name: "", email: "", phone: "", address: "" });
    setShowModal(false);
    console.log("Order Response:", orderResponse.data);
    } catch (error) {
      const errorMsg = error.response?.data?.detail;
      setShowModal(false);
      // toastr.error(errorMsg);
    }
  };
  
  return (
    <div className="container mt-5">
      <h2 className="text-center mb-4">Consumer Dashboard</h2>
      
     Display user balance if available
     {balance !== null && (
      <div className="alert alert-info">
        <strong>Your Balance:</strong> ${balance.toFixed(2)}
      </div>
    )}

      <div className="table-responsive">
        <table className="table table-bordered table-hover align-middle">
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
                <td colSpan="7" className="text-center text-muted">
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
                  <td className="text-center">
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

      <div className="d-flex justify-content-end">
        <Button variant="success" onClick={handleOpenModal}>
          Buy Selected ({cart.length})
        </Button>
      </div>

      {/* Bootstrap Modal */}
      <Modal show={showModal} onHide={handleCloseModal}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Your Order</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3" controlId="name">
              <Form.Label>Full Name</Form.Label>
              <Form.Control
                type="text"
                name="name"
                value={form.name}
                onChange={handleFormChange}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="email">
              <Form.Label>Email</Form.Label>
              <Form.Control
                type="email"
                name="email"
                value={form.email}
                onChange={handleFormChange}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="phone">
              <Form.Label>Phone Number</Form.Label>
              <Form.Control
                type="text"
                name="phone"
                value={form.phone}
                onChange={handleFormChange}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="address">
              <Form.Label>Delivery Address</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                name="address"
                value={form.address}
                onChange={handleFormChange}
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseModal}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleConfirmOrder}>
            Confirm Order
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default ConsumerDashboard;