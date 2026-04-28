import React, { useState } from 'react'

export default function App() {
  const [message, setMessage] = useState("")

  function handleSubmit(e) {
    e.preventDefault()
    setMessage("Booking request sent (backend will be connected next)")
  }

  return (
    <div style={{padding:20, fontFamily:"sans-serif"}}>
      <h1>LCM Oven & Carpet Cleaning</h1>
      <p>Book your cleaning service below</p>

      <form onSubmit={handleSubmit}>
        <input placeholder="Name" required /><br/><br/>
        <input placeholder="Address" required /><br/><br/>
        <input placeholder="Postcode" required /><br/><br/>
        <input type="date" required /><br/><br/>
        <input type="time" required /><br/><br/>

        <button type="submit">Book</button>
      </form>

      <p>{message}</p>
    </div>
  )
}
