# OmniSight – UI Test Scenarios

## 1. Project Overview

**Project:** OmniSight Mock E-Commerce Website
**Purpose:** Define repeatable UI test scenarios to validate the website manually before automating with Playwright.

## 2. Test Scenarios

| Test ID | Feature | Test Steps | Expected Result |
|---|---|---|---|
| TC-01 | Website Loading | 1. Open the website in a browser | Homepage loads with no errors; header, navigation and products are visible |
| TC-02 | Product Display | 1. Go to Products | All six products appear, each with name, price and an Add to Cart button |
| TC-03 | Product Search | 1. Search for "Smart Watch" | Only the Smart Watch product appears |
| TC-04 | Category Filter | 1. Select Audio | Only audio products appear |
| TC-05 | Price Sorting | 1. Select Price: low to high | Products appear in ascending price order |
| TC-06 | Add to Cart | 1. Click Add to Cart on a product | Cart count increases by 1 and the product appears in the cart |
| TC-07 | Quantity Update | 1. Add a product 2. Increase its quantity | Quantity, subtotal and cart total update correctly |
| TC-08 | Remove Product | 1. Add a product 2. Click Remove | Product is removed; count and totals update |
| TC-09 | Empty Cart Checkout | 1. With an empty cart, click Checkout | A message asks the user to add a product |
| TC-10 | Invalid Checkout | 1. Add a product 2. Leave fields empty or enter invalid data 3. Submit | Validation errors appear and no order is placed |
| TC-11 | Successful Checkout | 1. Add a product 2. Enter valid details 3. Submit | Order confirmation appears |
| TC-12 | New Order | 1. After confirmation, click Start a new order | Checkout is available again with an empty cart |
| TC-13 | Responsive Layout | 1. Open the site at desktop width 2. Resize to mobile width | Content stays usable with no overlap or horizontal scrolling |

## 3. Test Execution Results

Record the actual result after running each test.

| Test ID | Actual Result | Status |
|---|---|---|
| TC-01 | To be tested | Pending |
| TC-02 | To be tested | Pending |
| TC-03 | To be tested | Pending |
| TC-04 | To be tested | Pending |
| TC-05 | To be tested | Pending |
| TC-06 | To be tested | Pending |
| TC-07 | To be tested | Pending |
| TC-08 | To be tested | Pending |
| TC-09 | To be tested | Pending |
| TC-10 | To be tested | Pending |
| TC-11 | To be tested | Pending |
| TC-12 | To be tested | Pending |
| TC-13 | To be tested | Pending |

## 4. Notes

- These scenarios are intended for manual testing first.
- Playwright automation can be added in a later stage.
- Record any failures with a screenshot and clear reproduction steps.
- Mark a test as Passed or Failed only after executing it.