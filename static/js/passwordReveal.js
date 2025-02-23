function myFunction() {
  var x = document.getElementById("typePasswordX-2");
  var y = document.getElementById("typePasswordX-3");
  if (x.type === "password") {
    x.type = "text";
    y.type = "text";
  } else {
    x.type = "password";
    y.type = "password";
  }
}