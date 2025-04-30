import React, { useState } from "react";
import Layout from "../../components/layout/Layout";
import { signup } from "../../api/auth";
import toastr from "toastr";
import "toastr/build/toastr.min.css";

// Role constants
const ROLES = {
  SUPPLIER: "supplier",
  MANUFACTURER: "manufacturer",
  LOGISTICS: "logistics",
  CONSUMER: "consumer",
  ADMIN: "admin",
};

export default function SignupPage() {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    role: ROLES.SUPPLIER, // default selected
  });

  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await signup(formData); 
      toastr.success("Signup successful! Please log in.");
      window.location.href = "/";
    } catch (err) {
      setError("Signup failed. Please check the details and try again.");
      toastr.error(err.response?.data || "Signup failed.");
      console.error("Signup error:", err.response?.data || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="card p-5 shadow-lg" style={{ maxWidth: "600px", width: "100%" }}>
        <h2 className="text-center mb-4">Sign Up</h2>
        {error && <div className="alert alert-danger">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="username" className="form-label">Username</label>
            <input
              type="text"
              className="form-control"
              id="username"
              name="username"
              placeholder="Choose a username"
              value={formData.username}
              onChange={handleChange}
              required
            />
          </div>
          <div className="mb-3">
            <label htmlFor="email" className="form-label">Email</label>
            <input
              type="email"
              className="form-control"
              id="email"
              name="email"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>
          <div className="mb-3">
            <label htmlFor="password" className="form-label">Password</label>
            <input
              type="password"
              className="form-control"
              id="password"
              name="password"
              placeholder="Enter your password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>
          <div className="mb-3">
            <label htmlFor="role" className="form-label">Role</label>
            <select
              className="form-select"
              id="role"
              name="role"
              value={formData.role}
              onChange={handleChange}
              required
            >
              {Object.entries(ROLES).map(([key, value]) => (
                <option key={key} value={value}>
                  {value.charAt(0).toUpperCase() + value.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <button type="submit" className="btn btn-primary w-100" disabled={loading}>
            {loading ? "Signing up..." : "Sign Up"}
          </button>
        </form>
        <div className="text-center mt-3">
          Already have an account? <a href="/">Log in</a>
        </div>
      </div>
    </Layout>
  );
};