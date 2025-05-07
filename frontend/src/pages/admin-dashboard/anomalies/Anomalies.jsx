import React, { useEffect, useState } from "react";
import axios from "axios";

const Anomalies = () => {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        const response = await axios.get("http://localhost:8000/flagged-products", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setAnomalies(response.data);
      } catch (err) {
        console.error(err);
        setError("Failed to load flagged products.");
      } finally {
        setLoading(false);
      }
    };

    fetchAnomalies();
  }, []);

  if (loading) return <p>Loading anomalies...</p>;
  if (error) return <p className="text-danger">{error}</p>;

  return (
    <div className="container mt-5">
      <h2>Anomalies</h2>
      <p className="mb-4">List of flagged products and supplier details:</p>

      <table className="table table-striped table-bordered">
        <thead className="table-dark">
          <tr>
            <th>Product ID</th>
            <th>Reason</th>
            <th>Detected At</th>
            <th>Supplier Name</th>
            <th>Supplier Email</th>
            <th>Product Name</th>
            <th>Product Price</th>
            <th>Product Category</th>
            <th>Product Ingredients</th>
          </tr>
        </thead>
        <tbody>
          {anomalies.length === 0 ? (
            <tr>
              <td colSpan={5} className="text-center">
                No anomalies found.
              </td>
            </tr>
          ) : (
            anomalies.map((item) => (
              <tr key={item.id}>
                <td>{item.product_id}</td>
                <td>{item.reason}</td>
                <td>{new Date(item.created_at).toLocaleString()}</td>
                <td>{item.supplier.username}</td>
                <td>{item.supplier.email}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default Anomalies;