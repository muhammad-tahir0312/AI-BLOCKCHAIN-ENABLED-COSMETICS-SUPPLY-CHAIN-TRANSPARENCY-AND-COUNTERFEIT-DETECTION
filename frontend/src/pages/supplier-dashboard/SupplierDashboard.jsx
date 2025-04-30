import React, { useState, useEffect } from "react";
import axios from "axios";
import { jwtDecode } from "jwt-decode";
import toastr from "toastr";
import "toastr/build/toastr.min.css";
import { Modal, Button } from "react-bootstrap";

const SupplierDashboard = () => {
  const [products, setProducts] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [product, setProduct] = useState({
    product_name: "",
    description: "",
    category: "",
    price: "",
    origin: "",
    ingredients: "",
    label: "",
  });

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const token = localStorage.getItem("token");

  useEffect(() => {
    try {
      const decoded = jwtDecode(token);
      if (decoded.role !== "supplier") {
        window.location.href = "/";
        return;
      }
    } catch {
      window.location.href = "/";
      return;
    }
    // fetchProducts();
  }, [token]);

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
      setError(errorMsg);
      toastr.error(errorMsg);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setProduct((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    try {
      const response = await axios.post("http://localhost:8000/products", product, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      const res = response.data;
      if (res.status === "warning" || res.status === "partial_success") {
        toastr.warning(res.message);
        setMessage(res.message);
      } else {
        toastr.success("Product registered successfully!");
        setMessage("Product registered successfully!");
        fetchProducts();
        setShowModal(false);
      }

      setProduct({
        product_name: "",
        description: "",
        category: "",
        price: "",
        origin: "",
        ingredients: "",
        label: "",
      });
    } catch (err) {
      const details = err.response?.data?.detail;
      const errorMsg = Array.isArray(details)
        ? details.map((d) => d.msg).join(", ")
        : details || "Product registration failed.";

      toastr.error(errorMsg);
      setError(errorMsg);
    }
  };

  return (
    <div className="container mt-5">
      <h2 className="text-center mb-4">Supplier Dashboard</h2>

      <div className="text-end mb-3">
        <Button onClick={() => setShowModal(true)}>Add Product</Button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

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
              <th>Label</th>
            </tr>
          </thead>
          <tbody>
            {products.length === 0 ? (
              <tr>
                <td colSpan="7" className="text-center">
                  No products found.
                </td>
              </tr>
            ) : (
              products.map((p) => (
                <tr key={p.id}>
                  <td>{p.product_name}</td>
                  <td>{p.description}</td>
                  <td>{p.category}</td>
                  <td>{p.origin}</td>
                  <td>${p.price}</td>
                  <td style={{ whiteSpace: "pre-wrap" }}>{p.ingredients}</td>
                  <td>{p.label}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal show={showModal} onHide={() => setShowModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Add Product</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {message && <div className="alert alert-success">{message}</div>}
          {error && <div className="alert alert-danger">{error}</div>}
          <form onSubmit={handleSubmit}>
            {[{ name: "product_name", label: "Product Name" },
              { name: "description", label: "Description" },
              { name: "category", label: "Category" },
              { name: "origin", label: "Origin" },
              { name: "price", label: "Price", type: "number" },
              { name: "ingredients", label: "Ingredients" },
              { name: "label", label: "Label" }].map(({ name, label, type = "text" }) => (
                <div className="mb-3" key={name}>
                  <label htmlFor={name} className="form-label">{label}</label>
                  {name === "ingredients" ? (
                    <textarea
                      className="form-control"
                      id={name}
                      name={name}
                      rows={3}
                      value={product[name]}
                      onChange={handleChange}
                      required
                    />
                  ) : (
                    <input
                      type={type}
                      className="form-control"
                      id={name}
                      name={name}
                      value={product[name]}
                      onChange={handleChange}
                      required
                    />
                  )}
                </div>
              ))}
            <Button variant="primary" type="submit" className="w-100">
              Submit Product
            </Button>
          </form>
        </Modal.Body>
      </Modal>
    </div>
  );
};

export default SupplierDashboard;