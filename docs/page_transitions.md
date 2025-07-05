# Page Transition Utilities

Smooth page transitions help the dashboard feel responsive without causing layout shifts.  The
`assets/css/07-utilities/_transitions.css` file introduces a small set of classes for this purpose.

- `transition-fade-move` – sets up coordinated opacity and transform transitions using the project
  timing variables.
- `transition-start` – hidden starting state that keeps the element in flow.
- `transition-end` – visible end state after content loads.
- `transition-fix` – promotes the element to its own layer to reduce jank.

Example usage:

```html
<main id="page-content" class="main-content p-4 transition-fade-move transition-start"></main>
```

After the page content is ready, toggle the classes:

```python
@app.callback(
    Output("page-content", "className"),
    Input("url", "pathname")
)
def show_page(pathname):
    return "main-content p-4 transition-fade-move transition-end"
```
