import pygw2.api
import locale
from fastapi import FastAPI, Path, Query, Request
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pygw2.core.models import Price

from config import settings
from pydantic import BaseModel

app = FastAPI(root_path=settings.ROOT_PATH)


class Meta(BaseModel):
    version: str | None
    build: str | None


class GoldData(BaseModel):
    current: str
    target: str


def custom_openapi():
    # Return "cached" API schema
    if app.openapi_schema:
        return app.openapi_schema

    # Generate OpenAPI Schema
    openapi_schema = get_openapi(
        title="GW2 overlay things",
        version=f"{settings.VERSION}:{settings.BUILD}",
        routes=app.routes,
    )

    # Make fields that are not required nullable
    for name, component in openapi_schema["components"]["schemas"].items():
        if (
                "required" in component
                and component["required"]
                and "properties" in component
                and component["properties"]
        ):
            for f_name, field in component["properties"].items():
                if f_name not in component["required"]:
                    field["nullable"] = True

                # Update field
                component["properties"][f_name] = field
        # Update component
        openapi_schema["components"]["schemas"][name] = component

    # Save schema, so it doesn't have to be generated every time
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/meta", response_model=Meta)
def meta():
    return {"version": settings.VERSION, "build": settings.BUILD}


@app.get("/gold", response_class=HTMLResponse)
async def gold(request: Request, *,
               apikey: str = Query(..., description="GW2 API key"),
               item: str | None = Query(None, description="Item ID"),
               text: str = Query("Gold", description="pre text"),
               target: int = Query(0, description="target gold"),
               interval: int = Query(60, description="Interval of update in seconds")
               ):
    api = pygw2.api.Api(api_key=apikey)

    wallet = await api.account.wallet()

    gold_obj = [x for x in wallet if x.id == 1]
    gold_amount = gold_obj[0].value // (100 * 100)

    languages = [x.split(";")[0] for x in request.headers["accept-language"].split(",")]

    for language in languages:
        try:
            locale.setlocale(locale.LC_ALL, locale.normalize(language))
            break
        except:
            pass

    if item:
        item_obj = await api.items.get(item)
        prices = await api.commerce.prices(item_obj.id)
        image = f"<img src=\"{item_obj.icon}\" />"
        item_name = item_obj.name

        if isinstance(prices, list):
            prices = prices[0]

        if isinstance(prices, Price) and prices.buys and prices.buys.unit_price:
            target = prices.buys.unit_price // (100 * 100)

        if isinstance(prices, Price) and prices.sells and prices.sells.unit_price:
            target = prices.sells.unit_price // (100 * 100)

        body = f"""
        <div class="Row">
        <div class="Column"><p class="Text" id="text">Gold for {item_name} {gold_amount:n}/{target:n}</p></div>
        <div class="Column">{image}</div>
        </div>
        """

        text = f"Gold for {item_name}"

        params = f"""
        new URLSearchParams({{
            apikey: "{apikey}",
            item: "{item}",
        }})
        """
    else:
        body = f"""
        <div class="Row">
        <div class="Column"><p class="Text" id="text">{text} {gold_amount:n}/{target:n}</p></div>
        </div>
        """

        params = f"""
        new URLSearchParams({{
            apikey: "{apikey}",
            target: "{target}"
        }})
        """

    css = """
    <style>
        .Row {
        display: table;
    }
    .Column {
        display: table-cell;
        padding-left: 5px;
        padding-right: 5px;
        text-align: center;
        vertical-align: middle;
    }
    .Text {
        font-size: 2em;
        color: #FFD700;
        -webkit-text-stroke: 1px white;
        font-family: "Lucida Console", "Courier New", monospace;
        font-weight: bold;
    }
    
    body {
        background-color: transparent;
    }

    </style>
    """

    js = f"""
    <script>
    const text = "{text}";
    async function updateText() {{
        const textElem = document.getElementById("text");
        const response = await fetch("/gold_data?" + {params});
        const data = await response.json();
        textElem.innerText = text + " " + data.current + "/" + data.target;
    }}
    setInterval(updateText, {interval}*1000)
    </script>
    """

    return f"""
        <html>
            <head>
                {css}
                {js}
                <title>Gold overlay</title>
            </head>
            <body>
                {body}
            </body>
        </html>
        """


@app.get("/gold_data", response_model=GoldData)
async def gold(request: Request, *,
               apikey: str = Query(..., description="GW2 API key"),
               item: str | None = Query(None, description="Item ID"),
               target: int = Query(0, description="target gold")
               ):
    api = pygw2.api.Api(api_key=apikey)

    wallet = await api.account.wallet()

    gold_obj = [x for x in wallet if x.id == 1]
    gold_amount = gold_obj[0].value // (100 * 100)

    languages = [x.split(";")[0] for x in request.headers["accept-language"].split(",")]

    for language in languages:
        try:
            locale.setlocale(locale.LC_ALL, locale.normalize(language))
            break
        except:
            pass

    if item:
        prices = await api.commerce.prices(item)

        if isinstance(prices, list):
            prices = prices[0]

        if isinstance(prices, Price) and prices.buys and prices.buys.unit_price:
            target = prices.buys.unit_price // (100 * 100)

        if isinstance(prices, Price) and prices.sells and prices.sells.unit_price:
            target = prices.sells.unit_price // (100 * 100)

    return GoldData(**{
        "current": f"{gold_amount:n}",
        "target": f"{target:n}"
    })
