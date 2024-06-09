async function cookiesGate() {
  try {
    const domain = "http://127.0.0.1:8000";
    const response = await fetch(domain + "/process-cookies/", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        owner_name: "Ademola",
      }),
    });

    const result = await response.json();

    if (response.ok) {
      console.log(result.message);
      console.log("message success");
    } else {
      console.log(`Error: ${result.detail}`);
      console.log("message error");
    }
  } catch (error) {
    console.log(`Error: ${error.message}`);
    console.log("message error");
  }
}
// call it when you want it to start extract
cookiesGate();
