import AppRoutes from "./routes";
import toastr from "toastr";
import "toastr/build/toastr.min.css";

toastr.options = {
  closeButton: true,
  progressBar: true,
  positionClass: "toast-bottom-right",
  timeOut: "5000",
  extendedTimeOut: "1000",
  preventDuplicates: true,
  newestOnTop: true,
};

// Custom CSS for toastr
const toastrStyle = document.createElement("style");
toastrStyle.innerHTML = `
  #toast-container > .toast {
    background-color: red !important; /* Red background */
    color: white !important; /* White text */
  }
  #toast-container > .toast-success {
    background-color: red !important; /* Override success toast */
  }
  #toast-container > .toast-error {
    background-color: red !important; /* Override error toast */
  }
`;
document.head.appendChild(toastrStyle);

function App() {
  return <AppRoutes />;
}

export default App;