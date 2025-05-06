import React, { useState, useEffect } from "react";
import toastr from "toastr";
import "toastr/build/toastr.min.css";
import axios from "axios";
import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";
import Table from "react-bootstrap/Table";

const Verify = () => {
  const [showModal, setShowModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);
  const [orderIdInput, setOrderIdInput] = useState("");
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const token = localStorage.getItem("token");

  // Fetch user's orders
  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const response = await axios.get("http://localhost:8000/orders/my-orders", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setOrders(response.data);
      } catch (err) {
        setError("Failed to load your orders.");
        toastr.error("Failed to load orders");
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, []);

  const openModal = (order) => {
    setSelectedOrder(order);
    setVerificationResult(null);
    setOrderIdInput(order.id.toString()); // pre-fill with order ID
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
  };

  const handleVerify = async () => {
    if (!orderIdInput.trim()) {
      toastr.warning("Please enter an Order ID.");
      return;
    }

    try {
      const res = await axios.get(`http://localhost:8000/orders/${orderIdInput}/ledger`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.data && res.data.length > 0) {
        setVerificationResult("trusted");
      } else {
        setVerificationResult("counterfeit");
      }
    } catch (err) {
      console.error(err);
      setVerificationResult("counterfeit");
    }
  };

  const statusBadge = (status) => {
    if (status === "trusted") {
      return <span className="badge bg-success">Verified</span>;
    } else if (status === "counterfeit") {
      return <span className="badge bg-danger">Unverified</span>;
    } else {
      return null;
    }
  };

  return (
    <div className="container mt-5">
      <h2>Verify Orders</h2>

      {loading ? (
        <p>Loading your orders...</p>
      ) : error ? (
        <p className="text-danger">{error}</p>
      ) : (
        <Table striped bordered hover responsive>
          <thead className="table-light">
            <tr>
              <th>Order ID</th>
              <th>Customer Name</th>
              <th>Status</th>
              <th>Date</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center">
                  No orders found.
                </td>
              </tr>
            ) : (
              orders.map((order) => (
                <tr key={order.id}>
                  <td>{order.id}</td>
                  <td>{order.customer_name}</td>
                  <td>{order.status}</td>
                  <td>{new Date(order.created_at).toLocaleDateString()}</td>
                  <td>
                    <Button variant="outline-primary" size="sm" onClick={() => openModal(order)}>
                      Verify
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </Table>
      )}

      {/* Verification Modal */}
      <Modal show={showModal} onHide={closeModal}>
        <Modal.Header closeButton>
          <Modal.Title>Verify Order #{selectedOrder?.id}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <label htmlFor="orderId" className="form-label">
            Enter Order ID or Blockchain Transaction Hash
          </label>
          <input
            id="orderId"
            type="text"
            className="form-control mb-3"
            value={orderIdInput}
            onChange={(e) => setOrderIdInput(e.target.value)}
          />

          {verificationResult && (
            <div className="mt-3">
              <strong>Status:</strong> {statusBadge(verificationResult)}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={closeModal}>
            Close
          </Button>
          <Button variant="primary" onClick={handleVerify}>
            Verify
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default Verify;