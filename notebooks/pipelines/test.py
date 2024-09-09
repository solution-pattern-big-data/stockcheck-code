
import kfp.compiler
from kfp import dsl
from kfp.dsl import InputPath, OutputPath

#

@dsl.component(base_image="image-registry.openshift-image-registry.svc:5000/openshift/python:latest",
               packages_to_install=["yfinance", "pandas"])
def download_data(data_path: OutputPath()):
    import yfinance as yfin
    import pandas as pd
    """Calculate the sum of the two arguments."""
    #ticker = os.environ.get('TICKER')
    ticker = 'AAPL'
    df = yfin.download(tickers=ticker, period='6mo')
    dataset = df['Close'].fillna(method='ffill')
    dataset = dataset.values.reshape(-1, 1)
    print(dataset.shape)
    data = pd.DataFrame(dataset)
    data.to_csv('data.csv', header=False, index=False)
    
    
@dsl.pipeline()
def add_pipeline(ticker: str = 'AAPL'):
    """Pipeline to add values.
    """
    first_task = download_data()
    csv_file = first_task.outputs["data_path"]
    print(csv_file)

if __name__ == "__main__":
    kfp.compiler.Compiler().compile(add_pipeline, package_path=__file__.replace(".py", ".yaml"))