# OmniSight – UI Test Scenarios

## 1. Project Overview

**Project:** OmniSight Mock E-Commerce Website  
**Purpose:** To define repeatable UI test scenarios for validating website functionality before automating tests.

## 2. Test Scenarios

| Test ID | Feature | Test Steps | Expected Result |
|---|---|---|---|
| TC-01 | Website Loading | Open the website in a browser | The homepage loads correctly |
| TC-02 | Product Display | Navigate to Products | All six products appear |
| TC-03 | Product Search | Search for "Smart Watch" | The matching product appears |
| TC-04 | Category Filter | Select Audio | Only audio products appear |
| TC-05 | Price Sorting | Select Price: low to high | Products appear in ascending price order |
| TC-06 | Add to Cart | Add a product to the cart | The cart count increases |
| TC-07 | Quantity Update | Increase a product's quantity | Quantity and total update correctly |
| TC-08 | Remove Product | Remove a product from the cart | The product is removed and totals update |
| TC-09 | Empty Cart Checkout | Attempt checkout with an empty cart | A message asks the user to add a product |
| TC-10 | Invalid Checkout | Submit incomplete or invalid details | Validation errors are displayed |
| TC-11 | Successful Checkout | Add a product and submit valid details | An order confirmation appears |
| TC-12 | New Order | Select Start a new order | The checkout process becomes available again |
| TC-13 | Responsive Layout | Open the website at desktop and mobile widths | Content remains usable at both sizes |

## 3. Test Execution Results

Record the actual result after running each test.

| Test ID | Actual Result | Status |
|---|---|---|
| TC-01 | Homepage loaded successfully | Passed |
| TC-02 | All six products displayed successfully | Passed |
| TC-03 | Smart Watch displayed after search | Passed |
| TC-04 | Only three audio products displayed | Passed |
| TC-05 | Products displayed in ascending price order | Passed |
| TC-06 | Product added successfully and cart count increased to 1 | Passed |
| TC-07 | Product quantity increased from 1 to 2 successfully | Passed |
| TC-08 | Product removed and cart totals updated successfully | Passed |
| TC-09 | Empty cart checkout displays a message asking to add a product | Passed |
| TC-10 | Validation errors displayed for invalid checkout details | Passed |
| TC-11 | Order placed successfully with valid checkout details | Passed |
| TC-12 | Start a new order successfully after completing checkout | Passed |
| TC-13 | Website layout remains usable at desktop and mobile widths | Passed |

## 4. Notes

- These scenarios are intended for manual testing first.
- Playwright automation can be added in a later stage.
- Record any failures with screenshots and clear reproduction steps.
- Mark a test as Passed or Failed only after executing it.