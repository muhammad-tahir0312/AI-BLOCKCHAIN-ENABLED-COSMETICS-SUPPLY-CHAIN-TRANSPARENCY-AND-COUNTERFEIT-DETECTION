import { Routes, Route } from "react-router-dom";
import AppLayout from "../components/layout/Layout";
import 'bootstrap/dist/css/bootstrap.min.css';
import LoginPage from "../pages/login/LoginPage";
import SignupPage from "../pages/signup/SignupPage";
import AdminDashboard from "../pages/admin-dashboard/AdminDashboard";
import Shipments from "../pages/admin-dashboard/shipments/Shipments";
import Anomalies from "../pages/admin-dashboard/anomalies/Anomalies";
import Products from "../pages/admin-dashboard/products/Products";

import SupplierDashboard from "../pages/supplier-dashboard/SupplierDashboard";
import RegisterProduct from "../pages/supplier-dashboard/register-product/RegisterProduct";

import ConsumerDashboard from "../pages/consumer-dashboard/ConsumerDashboard";
import Verify from "../pages/consumer-dashboard/verify/Verify";
import LogisticDashboard from "../pages/logistic-dashboard/LogisticDashboard";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route element={<AppLayout />}>
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/products" element={<Products />} />
        <Route path="/admin/shipments" element={<Shipments />} />
        <Route path="/admin/anomalies" element={<Anomalies />} />

        <Route path="/supplier" element={<SupplierDashboard />} />
        <Route path="/supplier/register-product" element={<RegisterProduct />} />

        <Route path="/logistic" element={<LogisticDashboard />} />
        <Route path="/logistic/register-product" element={<RegisterProduct />} />

        <Route path="/consumer" element={<ConsumerDashboard />} />
        <Route path="/consumer/verify" element={<Verify />} />
      </Route>
    </Routes>
  );
}