import React,{useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import axios from 'axios';
import {Line,Bar} from 'react-chartjs-2';
import {Chart as ChartJS,CategoryScale,LinearScale,PointElement,LineElement,BarElement,Tooltip,Legend} from 'chart.js';
import './style.css';
ChartJS.register(CategoryScale,LinearScale,PointElement,LineElement,BarElement,Tooltip,Legend);

const API='http://127.0.0.1:8000';


function Forecast({ products = [] }) {

  const [productId, setProductId] = React.useState("");
  const [result, setResult] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  const getForecast = async () => {

    if (!productId) {
      setError("Please select a product");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {

      const response = await fetch(
        `http://127.0.0.1:8000/ml/forecast?product_id=${productId}`
      );

      const data = await response.json();

      if (!response.ok || data.error) {
        throw new Error(
          data.error || "Forecast failed"
        );
      }

      setResult(data);

    } catch (err) {

      setError(err.message);

    } finally {

      setLoading(false);

    }
  };


  const forecastLabels =
    result?.forecast?.map(x => x.date) || [];

  const forecastValues =
    result?.forecast?.map(
      x => x.predicted_demand
    ) || [];


  const forecastChart = {

    labels: forecastLabels,

    datasets: [
      {
        label: "Predicted Demand",

        data: forecastValues,

        borderWidth: 3,

        tension: 0.3,
        pointRadius:5,
        fill:false
      }
    ]
  };


  return (

    <div>

      <h1>Demand Forecasting</h1>

      <p>
        Predict future product demand using
        Machine Learning.
      </p>


      <section>

        <h2>Select Product</h2>

        <select
          value={productId}
          onChange={(e) =>
            setProductId(e.target.value)
          }
        >

          <option value="">
            Select Product
          </option>

          {products.map(product => (

            <option
              key={product.id}
              value={product.id}
            >
              {product.name}
            </option>

          ))}

        </select>


        <button
          onClick={getForecast}
          disabled={loading}
        >

          {loading
            ? "Predicting..."
            : "Predict Demand"}

        </button>

      </section>


      {error && (

        <p>
          ❌ {error}
        </p>

      )}


      {result && (

        <>

          <div className="grid2">

            <section>

              <h2>Product</h2>

              <h3>
                {result.product.name}
              </h3>

              <p>
                Current Stock:
                <b>
                  {" "}
                  {result.product.current_stock}
                </b>
              </p>

            </section>


            <section>

              <h2>Recommendation</h2>

              <h3>
                {result.recommendation}
              </h3>

              <p>
                Predicted 7-Day Demand:
                <b>
                  {" "}
                  {result.total_predicted_demand}
                </b>
              </p>

            </section>

          </div>


          <section>

            <h2>7-Day Demand Forecast</h2>

            <Line
  data={forecastChart}
  options={{
    responsive: true,
    plugins: {
      legend: {
        display: true
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: "Demand (Units)"
        }
      },
      x: {
        title: {
          display: true,
          text: "Date"
        }
      }
    }
  }}
/>

          </section>


          <section>

            <h2>Model Performance</h2>

            <div className="grid3">

              <div>
                <h3>MAE</h3>
                <p>
                  {result.metrics.mae}
                </p>
              </div>

              <div>
                <h3>RMSE</h3>
                <p>
                  {result.metrics.rmse}
                </p>
              </div>

              <div>
                <h3>R²</h3>
                <p>
                  {result.metrics.r2}
                </p>
              </div>

            </div>

            <p>
              Model:
              <b>
                {" "}
                {result.model}
              </b>
            </p>

          </section>


          <section>

            <h2>Daily Predictions</h2>

            <table>

              <thead>

                <tr>
                  <th>Date</th>
                  <th>Predicted Demand</th>
                </tr>

              </thead>

              <tbody>

                {result.forecast.map(item => (

                  <tr key={item.date}>

                    <td>
                      {item.date}
                    </td>

                    <td>
                      {item.predicted_demand}
                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </section>

        </>

      )}

    </div>
  );
}

function App(){
 const [tab,setTab]=useState('dashboard'); const [products,setProducts]=useState([]);
 const [analytics,setAnalytics]=useState({kpis:{},daily_sales:[],top_products:[]});
 const [segments,setSegments]=useState([]); const [rules,setRules]=useState([]);
 const [forecast,setForecast]=useState([]); const [selected,setSelected]=useState('');
 const [form,setForm]=useState({name:'',category:'Grocery',price:'',stock:'',reorder_level:10});
 const load=async()=>{setProducts((await axios.get(API+'/products')).data);setAnalytics((await axios.get(API+'/analytics')).data)};
 useEffect(()=>{load()},[]);
 const add=async e=>{e.preventDefault();await axios.post(API+'/products',{...form,price:+form.price,stock:+form.stock,reorder_level:+form.reorder_level});setForm({name:'',category:'Grocery',price:'',stock:'',reorder_level:10});load()};
 const remove=async id=>{await axios.delete(API+'/products/'+id);load()};
 const loadForecast=async id=>{setSelected(id);setForecast((await axios.get(API+'/ml/forecast/'+id)).data.predictions)};
 const loadSegments=async()=>setSegments((await axios.get(API+'/ml/segments')).data);
 const loadRules=async()=>setRules((await axios.get(API+'/data-mining/apriori')).data);
 const nav=(x)=>{setTab(x);if(x==='segments')loadSegments();if(x==='basket')loadRules()};
 return <div className="app">
  <aside><div className="brand">Smart Retail<br/><span>Intelligence</span></div>
   {['dashboard','inventory','sales','forecast','segments','basket'].map(x => (
  <button
    key={x}
    onClick={() => nav(x)}
  >
    {x}
  </button>
))}
   <div className="side-note">Smarter Decisions<br/>for Smarter Retail</div>
  </aside>
  <main><header><div><h1>{tab==='dashboard'?'Dashboard':tab==='basket'?'Market Basket Analysis':tab==='segments'?'Customer Segmentation':tab==='forecast'?'Demand Forecasting':'Inventory Management'}</h1><p>Classical ML • Data Mining • Business Analytics</p></div></header>
  {tab==='dashboard'&&<Dashboard a={analytics}/>}
  {tab==='inventory'&&
  <Inventory
    products={products}
    form={form}
    setForm={setForm}
    add={add}
    remove={remove}
    load={load}
  />
}
{tab==='sales'&&
  <Sales
    products={products}
    load={load}
  />
}
  {tab === "forecast" && (
  <Forecast products={products} />
)}
  {tab==='segments'&&<Segments data={segments}/>}
  {tab==='basket'&&<Basket data={rules}/>}
  </main></div>
}

function Cards({k}) {

  return (

    <div className="cards">

      <div>
        <small>Total Revenue</small>

        <b>
          ₹{Number(k.revenue || 0).toLocaleString()}
        </b>
      </div>


      <div>
        <small>Total Sales</small>

        <b>
          {k.sales || 0}
        </b>
      </div>


      <div>
        <small>Average Order Value</small>

        <b>
          ₹{Number(
            k.average_order_value || 0
          ).toFixed(2)}
        </b>
      </div>


      <div>
        <small>Low Stock</small>

        <b>
          {k.low_stock || 0}
        </b>
      </div>

    </div>

  );
}
function Dashboard({a}) {

  const dailySales = a?.daily_sales || [];
  const monthlySales = a?.monthly_sales || [];
  const topProducts = a?.top_products || [];
  const categorySales = a?.category_sales || [];

  const kpis = a?.kpis || {
    revenue: 0,
    sales: 0,
    products: 0,
    low_stock: 0,
    average_order_value: 0
  };


  const dailyChart = {
    labels: dailySales.map(
      x => x.sale_date
    ),

    datasets: [
      {
        label: 'Daily Revenue',

        data: dailySales.map(
          x => x.revenue
        )
      }
    ]
  };


  const topProductChart = {
    labels: topProducts.map(
      x => x.name
    ),

    datasets: [
      {
        label: 'Units Sold',

        data: topProducts.map(
          x => x.quantity
        )
      }
    ]
  };


  const categoryChart = {
    labels: categorySales.map(
      x => x.category
    ),

    datasets: [
      {
        label: 'Category Revenue',

        data: categorySales.map(
          x => x.revenue
        )
      }
    ]
  };


  const monthlyChart = {
    labels: monthlySales.map(
      x => x.month
    ),

    datasets: [
      {
        label: 'Monthly Revenue',

        data: monthlySales.map(
          x => x.revenue
        )
      }
    ]
  };


  return (
    <>

      <Cards k={kpis} />


      <div className="grid2">

        <section>

          <h2>Daily Sales Trend</h2>

          <Line data={dailyChart} />

        </section>


        <section>

          <h2>Top Selling Products</h2>

          <Bar data={topProductChart} />

        </section>

      </div>


      <div className="grid2">

        <section>

          <h2>Category-wise Revenue</h2>

          <Bar data={categoryChart} />

        </section>


        <section>

          <h2>Monthly Revenue</h2>

          <Line data={monthlyChart} />

        </section>

      </div>


      <section>

        <h2>Business Insights</h2>

        <p>
          Total revenue generated:
          <b>
            ₹{Number(kpis.revenue || 0).toLocaleString()}
          </b>
        </p>

        <p>
          Average order value:
          <b>
            ₹{Number(
              kpis.average_order_value || 0
            ).toFixed(2)}
          </b>
        </p>

        <p>
          Products requiring restocking:
          <b>
            {kpis.low_stock || 0}
          </b>
        </p>

      </section>

    </>
  );
}
function Inventory({products, form, setForm, add, remove, load}) {

  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [editingId, setEditingId] = useState(null);

  const categories = [
    'All',
    ...new Set(products.map(p => p.category))
  ];

  const filteredProducts = products.filter(p => {

    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase());

    const matchesCategory =
      category === 'All' || p.category === category;

    return matchesSearch && matchesCategory;
  });

  const startEdit = (product) => {

    setEditingId(product.id);

    setForm({
      name: product.name,
      category: product.category,
      price: product.price,
      stock: product.stock,
      reorder_level: product.reorder_level
    });
  };

  const cancelEdit = () => {

    setEditingId(null);

    setForm({
      name: '',
      category: 'Grocery',
      price: '',
      stock: '',
      reorder_level: 10
    });
  };

  const updateProduct = async (e) => {

    e.preventDefault();

    try {

      await axios.put(
        API + '/products/' + editingId,
        {
          name: form.name,
          category: form.category,
          price: Number(form.price),
          stock: Number(form.stock),
          reorder_level: Number(form.reorder_level)
        }
      );

      alert('Product updated successfully');

      cancelEdit();

      load();

    } catch (error) {

      console.error(error);

      alert('Error updating product');
    }
  };

  return (
    <>

      {/* ADD / EDIT PRODUCT */}

      <section>

        <h2>
          {editingId ? 'Edit Product' : 'Add Product'}
        </h2>

        <form
          className="form"
          onSubmit={editingId ? updateProduct : add}
        >

          <input
            required
            placeholder="Product name"
            value={form.name}
            onChange={e =>
              setForm({
                ...form,
                name: e.target.value
              })
            }
          />

          <input
            required
            placeholder="Category"
            value={form.category}
            onChange={e =>
              setForm({
                ...form,
                category: e.target.value
              })
            }
          />

          <input
            required
            type="number"
            placeholder="Price"
            value={form.price}
            onChange={e =>
              setForm({
                ...form,
                price: e.target.value
              })
            }
          />

          <input
            required
            type="number"
            placeholder="Stock"
            value={form.stock}
            onChange={e =>
              setForm({
                ...form,
                stock: e.target.value
              })
            }
          />

          <input
            required
            type="number"
            placeholder="Reorder level"
            value={form.reorder_level}
            onChange={e =>
              setForm({
                ...form,
                reorder_level: e.target.value
              })
            }
          />

          <button className="primary">

            {editingId
              ? 'Update Product'
              : 'Add Product'}

          </button>

          {editingId && (

            <button
              type="button"
              onClick={cancelEdit}
            >
              Cancel
            </button>

          )}

        </form>

      </section>


      {/* SEARCH AND FILTER */}

      <section>

        <h2>Search & Filter</h2>

        <div className="form">

          <input
            placeholder="Search product..."
            value={search}
            onChange={e =>
              setSearch(e.target.value)
            }
          />

          <select
            value={category}
            onChange={e =>
              setCategory(e.target.value)
            }
          >

            {categories.map(c => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}

          </select>

        </div>

      </section>


      {/* INVENTORY TABLE */}

      <section>

        <h2>
          Inventory ({filteredProducts.length})
        </h2>

        <table>

          <thead>

            <tr>

              <th>Product</th>

              <th>Category</th>

              <th>Price</th>

              <th>Stock</th>

              <th>Status</th>

              <th>Action</th>

            </tr>

          </thead>

          <tbody>

            {filteredProducts.map(p => (

              <tr key={p.id}>

                <td>{p.name}</td>

                <td>{p.category}</td>

                <td>₹{p.price}</td>

                <td>{p.stock}</td>

                <td>

                  <span
                    className={
                      p.stock <= p.reorder_level
                        ? 'danger'
                        : 'ok'
                    }
                  >

                    {p.stock <= p.reorder_level
                      ? 'Low Stock'
                      : 'Available'}

                  </span>

                </td>

                <td>

                  <button
                    onClick={() => startEdit(p)}
                  >
                    Edit
                  </button>

                  <button
                    onClick={() => remove(p.id)}
                    style={{marginLeft: '8px'}}
                  >
                    Delete
                  </button>

                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </section>

    </>
  );
}

function Segments({data}){return <section><h2>Customer Segments</h2><table><thead><tr><th>Customer</th><th>Spending</th><th>Purchases</th><th>AOV</th><th>Cluster</th></tr></thead><tbody>{data.map(x=><tr><td>{x.name}</td><td>₹{x.total_spending}</td><td>{x.purchases}</td><td>₹{x.avg_order_value}</td><td>Cluster {x.cluster}</td></tr>)}</tbody></table><p className="hint">Clusters are mathematical groups, not fixed customer labels. Interpret them after examining their feature averages.</p></section>}
function Basket({data}){return <section><h2>Association Rules</h2><table><thead><tr><th>Antecedent</th><th>Consequent</th><th>Support</th><th>Confidence</th><th>Lift</th></tr></thead><tbody>{data.map(x=><tr><td>{x.antecedent}</td><td>{x.consequent}</td><td>{x.support}</td><td>{x.confidence}</td><td>{x.lift}</td></tr>)}</tbody></table></section>}
function Sales({products, load}) {

  const [customerId, setCustomerId] = useState(1);

  const [cart, setCart] = useState([]);

  const [productId, setProductId] = useState('');

  const [quantity, setQuantity] = useState(1);


  const addToCart = () => {

    if (!productId) {
      alert('Please select a product');
      return;
    }

    const product = products.find(
      p => p.id === Number(productId)
    );

    if (!product) return;

    if (quantity <= 0) {
      alert('Quantity must be greater than 0');
      return;
    }

    if (quantity > product.stock) {
      alert('Not enough stock available');
      return;
    }

    const existing = cart.find(
      item => item.product_id === product.id
    );

    if (existing) {

      const newQuantity =
        existing.quantity + Number(quantity);

      if (newQuantity > product.stock) {
        alert('Not enough stock available');
        return;
      }

      setCart(
        cart.map(item =>
          item.product_id === product.id
            ? {...item, quantity: newQuantity}
            : item
        )
      );

    } else {

      setCart([
        ...cart,
        {
          product_id: product.id,
          name: product.name,
          price: product.price,
          quantity: Number(quantity)
        }
      ]);

    }

    setProductId('');
    setQuantity(1);
  };


  const removeFromCart = (id) => {

    setCart(
      cart.filter(
        item => item.product_id !== id
      )
    );

  };


  const total = cart.reduce(
    (sum, item) =>
      sum + item.price * item.quantity,
    0
  );


  const recordSale = async () => {

    if (cart.length === 0) {
      alert('Please add at least one product');
      return;
    }

    try {

      const saleData = {

        customer_id: Number(customerId),

        items: cart.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity
        }))

      };


      const response = await axios.post(
        API + '/sales',
        saleData
      );


      alert(
        'Sale recorded successfully! Total: ₹' +
        response.data.total
      );


      setCart([]);

      setCustomerId(1);

      load();

    } catch (error) {

      console.error(error);

      alert(
        error.response?.data?.detail ||
        'Error recording sale'
      );

    }

  };


  return (
    <>

      {/* SALE FORM */}

      <section>

        <h2>Record New Sale</h2>

        <div className="form">

          <input
            type="number"
            min="1"
            placeholder="Customer ID"
            value={customerId}
            onChange={e =>
              setCustomerId(e.target.value)
            }
          />


          <select
            value={productId}
            onChange={e =>
              setProductId(e.target.value)
            }
          >

            <option value="">
              Select Product
            </option>

            {products
              .filter(p => p.stock > 0)
              .map(p => (

                <option
                  key={p.id}
                  value={p.id}
                >

                  {p.name} -
                  ₹{p.price} -
                  Stock: {p.stock}

                </option>

              ))}

          </select>


          <input
            type="number"
            min="1"
            value={quantity}
            onChange={e =>
              setQuantity(e.target.value)
            }
          />


          <button
            className="primary"
            onClick={addToCart}
          >
            Add Product
          </button>

        </div>

      </section>


      {/* BILL */}

      <section>

        <h2>Current Bill</h2>

        {cart.length === 0 ? (

          <p>No products added yet.</p>

        ) : (

          <>

            <table>

              <thead>

                <tr>

                  <th>Product</th>

                  <th>Price</th>

                  <th>Quantity</th>

                  <th>Total</th>

                  <th>Action</th>

                </tr>

              </thead>


              <tbody>

                {cart.map(item => (

                  <tr key={item.product_id}>

                    <td>{item.name}</td>

                    <td>₹{item.price}</td>

                    <td>{item.quantity}</td>

                    <td>
                      ₹{item.price * item.quantity}
                    </td>

                    <td>

                      <button
                        onClick={() =>
                          removeFromCart(item.product_id)
                        }
                      >
                        Remove
                      </button>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>


            <div className="sale-total">

              <h2>
                Total: ₹{total.toFixed(2)}
              </h2>

              <button
                className="primary"
                onClick={recordSale}
              >
                Record Sale
              </button>

            </div>

          </>

        )}

      </section>

    </>
  );
}
createRoot(document.getElementById('root')).render(<App/>);
