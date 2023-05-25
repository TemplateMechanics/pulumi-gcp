This Python-based tool uses Pulumi to dynamically create cloud resources on Google Cloud Platform (GCP) based on a YAML configuration file.

## Dependencies
- Python 3.7+
- Pulumi
- Google Cloud SDK (if running locally)

Python packages:
- pulumi
- pulumi-google-native
- dataclass-wizard
- automapper

Install them with pip:
```bash
pip install pulumi pulumi-google-native dataclass-wizard automapper
```
## Usage

First, you need to setup Pulumi. You can create a free account on the [Pulumi website](https://app.pulumi.com/site/signup). After creating your account, login via the Pulumi CLI:

```bash
pulumi login
gcloud auth application-default login
```
Clone this repository and go to the directory of the project and run
```bash
venv\Scripts\activate
```
then
```bash
pulumi up
```
Populate the `config.yaml` file according to your needs here is a sample:
```yaml
teams:
  - name: team1
    services:
      - name: svc1
        environments:
          - name: labs
            project: gcp-iac-template
            location: northamerica-northeast1
            labels: 
              CreatedBy: Pulumi
            gcp_native: 
              buckets:
                - name: bucket-1
                  args:
                    storage_class: STANDARD
                    force_destroy: true
```
This command will start the deployment of your GCP resources as per your configuration in the `config.yaml` file. The `pulumi up` command shows a preview of the updates to be performed and prompts you to confirm the deployment.

Debugging and Logs

If you encounter any issues while deploying your infrastructure with Pulumi, you can view the logs to gain more insight into what went wrong. The Pulumi console provides detailed logs that can help you debug your infrastructure code.

To view the logs, follow these steps:

1. Open your web browser and navigate to the Pulumi Console. This is the URL provided as a permalink after each deployment.
2. Navigate to your specific project and select the update that you are interested in. You should see a list of all deployments or "updates" for your project.
3. Click on the specific update that you are interested in. This will bring you to a detailed page about that update.
4. On the update page, you can see a detailed log of all actions that Pulumi took during that update. This includes detailed error messages that can help you debug issues with your infrastructure code.

Additionally, you can use the `pulumi logs` command to fetch the logs of your most recent update.

```bash
pulumi logs
```
## Explanation and Deep Dive

This section serves to help understand some aspects of the code that may not be familiar to folks coming from a non-programming background:
```python
    async def replaceValue(self, args : any, propertyName : str, value : str | pulumi.Output[any]) -> str:
        newValue : str = value
        m = re.search(r"Resource (.+),\s?(.+)", value)
        if m is not None:
            resource = await self.context.get_resource_from_cache(m.group(1))
            newValue = getattr(resource, m.group(2)) or value
        else:
            m = re.search(r"Secret (.+)", value)
            if m is not None:
              secret = pulumiConfig.require_secret(m.group(1))
              newValue = secret or value

        if value != newValue:
            setattr(args, propertyName, newValue)
```
This piece of code is a function that replaces certain values within your data structure. It's part of the 'search-and-replace' operation mentioned below:

The function `replaceValue()` takes three arguments: 

1. `args`: This is the object that the function is currently looking at.
2. `propertyName`: This is the specific property within that object which the function is considering replacing.
3. `value`: This is the current value of that property.

It first defines a new variable `newValue` to be the same as the current `value`.

Then it checks if the current `value` matches the pattern "Resource <something>, <something>". If it does, it finds the corresponding resource from a cache and replaces the `value` with a property of that resource.

If the `value` does not match the "Resource" pattern, it checks if it matches the pattern "Secret <something>". If it does, it gets the corresponding secret from the Pulumi configuration and replaces the `value` with this secret.

If neither pattern matches, `newValue` remains the same as the original `value`.

Finally, if `newValue` is different from the original `value`, it replaces the original value with `newValue` in the `args` object.

In summary, this function is checking each value in your data structure to see if it should be replaced with a value from a resource or a secret. If it should, it performs the replacement.

Additionally we have this section:

```python
    async def replaceInputArgs(self, args: any):
        properties = [a for a in dir(args) if not a.startswith('__') and not callable(getattr(args, a))]
        for property in properties:
            value = getattr(args, property)
            if value is not None:

                # loop iterables
                if (isinstance(value, Iterable)):
                    for item in value:
                        await self.replaceInputArgs(item)

                # deep replace on all child dataclasses
                if (dataclasses.is_dataclass(value)):
                    await self.replaceInputArgs(value)

                # only replace values for strings
                if isinstance(value, str):
                    await self.replaceValue(args, property, value)
```
This section of the code is an asynchronous method called `replaceInputArgs` in the `ResourceBuilder` class. The purpose of this method is to iterate over the properties of an input argument object and recursively replace any string values.

Let's break down the method:

- `properties = [a for a in dir(args) if not a.startswith('__') and not callable(getattr(args, a))]`: This line is using a list comprehension to get a list of all the properties in the `args` object. The `dir()` function is used to get a list of all attributes of the object. The list comprehension filters out any attributes that start with '__' (these are usually system attributes), and any attributes that are callable (i.e., methods).

- `for property in properties`: This line starts a loop over all the properties that were just defined.

- `value = getattr(args, property)`: For each property, this line gets the current value of the property.

- `if value is not None`: This line checks if the current value is not `None`. If it is `None`, the loop simply continues to the next property.

- `if (isinstance(value, Iterable))`: This line checks if the current value is an iterable (like a list or a dictionary). If it is, the method calls itself recursively for each item in the iterable.

- `if (dataclasses.is_dataclass(value))`: This line checks if the current value is a dataclass. If it is, the method again calls itself recursively, because a dataclass can have its own properties that might need to be replaced.

- `if isinstance(value, str)`: Finally, this line checks if the current value is a string. If it is, the method calls another method, `replaceValue()`, to replace the string value.

This process is repeated for all properties in the `args` object and all their child properties if they are iterable or dataclasses, until all string values have been replaced.

This code is essentially a deep search-and-replace function for a given data structure. Here's a simple explanation:

It takes an input object (like a complex configuration file) and goes through all its properties one by one. If it finds a property that is a list, dictionary, or any other type of collection, it digs deeper into that collection and repeats the process.

If it comes across a property that is a more complex object (a 'dataclass' in Python), it again digs deeper, looking at all the properties of that object.

Now, if it finds a property that is a simple string, it does a 'replace' operation on it. The specifics of this replacement are defined in the `replaceValue()` method, which isn't shown here.

So in short, this code is designed to traverse complex nested data structures and perform a specific operation (in this case, a 'replace' operation) on every string it encounters.
