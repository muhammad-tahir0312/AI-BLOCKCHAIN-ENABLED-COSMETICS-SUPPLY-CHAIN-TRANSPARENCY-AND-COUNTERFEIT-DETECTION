import React, { useState, useEffect } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import { Tab, Tabs } from "react-bootstrap";
import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";

const LogisticDashboard = () => {
  const [key, setKey] = useState("NEW");
  const [orders, setOrders] = useState({
    NEW: [],
    CONFIRMED: [],
    DELIVERED: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [showModal, setShowModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [newStatus, setNewStatus] = useState("");

  const token = localStorage.getItem("token");

  // Fetch orders by status using /orders?status={status}
  const fetchOrdersByStatus = async (status) => {
    setLoading(true);
    setError("");
    try {
      const response = await axios.get(`http://localhost:8000/orders`, {
        params: { status },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setOrders((prev) => ({
        ...prev,
        [status]: response.data,
      }));
    } catch (err) {
      console.error("Failed to fetch orders:", err);
      setError("Failed to load orders.");
    } finally {
      setLoading(false);
    }
  };

  // Fetch data when tab changes
  useEffect(() => {
    if (!orders[key].length && token) {
      fetchOrdersByStatus(key);
    }
  }, [key]);

  const handleOpenModal = (order) => {
    setSelectedOrder(order);
    setNewStatus(
      order.status === "NEW" ? "CONFIRMED" : order.status === "CONFIRMED" ? "DELIVERED" : ""
    );
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedOrder(null);
  };

  const handleStatusChange = async () => {
    if (!selectedOrder || !newStatus) return;

    try {
      const response = await axios.put(
        `http://localhost:8000/orders/${selectedOrder.id}`,
        { status: newStatus },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      // Update local state
      setOrders((prev) => {
        const oldStatus = selectedOrder.status;
        return {
          ...prev,
          [oldStatus]: prev[oldStatus].filter((o) => o.id !== selectedOrder.id),
          [newStatus]: [...prev[newStatus], response.data],
        };
      });

      handleCloseModal();
    } catch (err) {
      console.error("Failed to update order status", err);
      alert("Failed to update order status.");
    }
  };

  return (
    <div className="container mt-5">
      <h2 className="mb-4">Logistic Dashboard</h2>

      <Tabs
        id="order-status-tabs"
        activeKey={key}
        onSelect={(k) => k && setKey(k)}
        className="mb-3"
      >
        <Tab eventKey="NEW" title="New Orders">
          <OrderTable
            orders={orders.NEW}
            loading={loading}
            error={error}
            onEdit={handleOpenModal}
            allowedNextStatus="CONFIRMED"
          />
        </Tab>
        <Tab eventKey="CONFIRMED" title="Confirmed Orders">
          <OrderTable
            orders={orders.CONFIRMED}
            loading={loading}
            error={error}
            onEdit={handleOpenModal}
            allowedNextStatus="DELIVERED"
          />
        </Tab>
        <Tab eventKey="DELIVERED" title="Delivered Orders">
          <OrderTable orders={orders.DELIVERED} loading={loading} error={error} />
        </Tab>
      </Tabs>

      {/* Status Update Modal */}
      <Modal show={showModal} onHide={handleCloseModal}>
        <Modal.Header closeButton>
          <Modal.Title>Update Order Status</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Order ID: {selectedOrder?.id}</Form.Label>
            <Form.Select value={newStatus} onChange={(e) => setNewStatus(e.target.value)}>
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="DELIVERED">DELIVERED</option>
            </Form.Select>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseModal}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleStatusChange}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

// Component to render table of orders
const OrderTable = ({ orders, loading, error, onEdit, allowedNextStatus }) => {
  if (loading) return <p>Loading...</p>;
  if (error) return <p className="text-danger">{error}</p>;

  return (
    <div className="table-responsive">
      <table className="table table-striped table-bordered">
        <thead className="table-dark">
          <tr>
            <th>Order ID</th>
            <th>Customer Name</th>
            <th>Contact</th>
            <th>Status</th>
            <th>Date</th>
            <th>Delivery Address</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {orders.length === 0 ? (
            <tr>
              <td colSpan={7} className="text-center">
                No orders found.
              </td>
            </tr>
          ) : (
            orders.map((order) => (
              <tr key={order.id}>
                <td>{order.id}</td>
                <td>{order.customer_name}</td>
                <td>{order.contact_number}</td>
                <td>
                  <span
                    className={`badge ${
                      order.status === "NEW"
                        ? "bg-secondary"
                        : order.status === "CONFIRMED"
                        ? "bg-primary"
                        : "bg-success"
                    }`}
                  >
                    {order.status}
                  </span>
                </td>
                <td>{new Date(order.created_at).toLocaleDateString()}</td>
                <td>{order.delivery_address}</td>
                <td>
                  {(allowedNextStatus === "CONFIRMED" ||
                    allowedNextStatus === "DELIVERED") && (
                    <button
                      className="btn btn-sm btn-outline-primary"
                      onClick={() => onEdit(order)}
                    >
                      Update Status
                    </button>
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default LogisticDashboard;