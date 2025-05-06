import React, { useState, useEffect } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import { Tab, Tabs } from "react-bootstrap";

const Shipments = () => {
  const [key, setKey] = useState("IN_TRANSIT");
  const [orders, setOrders] = useState({
    IN_TRANSIT: [],
    DELIVERED: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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

  return (
    <div className="container mt-5">
      <h2 className="mb-4">Shipments</h2>

      <Tabs
        id="shipment-status-tabs"
        activeKey={key}
        onSelect={(k) => k && setKey(k)}
        className="mb-3"
      >
        <Tab eventKey="IN_TRANSIT" title="In Transit">
          <OrderTable orders={orders.IN_TRANSIT} loading={loading} error={error} />
        </Tab>
        <Tab eventKey="DELIVERED" title="Delivered">
          <OrderTable orders={orders.DELIVERED} loading={loading} error={error} />
        </Tab>
      </Tabs>
    </div>
  );
};

// Component to render table of orders (read-only)
const OrderTable = ({ orders, loading, error }) => {
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
          </tr>
        </thead>
        <tbody>
          {orders.length === 0 ? (
            <tr>
              <td colSpan={6} className="text-center">
                No shipments found.
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
                      order.status === "CONFIRMED" || order.status === "IN_TRANSIT"
                        ? "bg-primary"
                        : "bg-success"
                    }`}
                  >
                    {order.status}
                  </span>
                </td>
                <td>{new Date(order.created_at).toLocaleDateString()}</td>
                <td>{order.delivery_address}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default Shipments;