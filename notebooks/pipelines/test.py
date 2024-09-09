
import kfp.compiler
from kfp import dsl

#
@dsl.component(base_image="image-registry.openshift-image-registry.svc:5000/openshift/python:latest",
               packages_to_install=["yfinance"])
def download_data():
    import yfinance as yfin
    """Calculate the sum of the two arguments."""
    #ticker = os.environ.get('TICKER')
    ticker = 'AAPL'
    df = yfin.download(tickers=ticker, period='6mo')
    dataset = df['Close'].fillna(method='ffill')
    dataset = dataset.values.reshape(-1, 1)

@dsl.pipeline()
def add_pipeline(ticker: str = 'AAPL'):
    """Pipeline to add values.
    """
    first_add_task = download_data()

if __name__ == "__main__":
    kfp.compiler.Compiler().compile(add_pipeline, package_path=__file__.replace(".py", ".yaml"))