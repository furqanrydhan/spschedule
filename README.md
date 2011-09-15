# StylePage tools: Python Job Scheduling

## Dependencies

This tool requires decorator, spmongo and access to a MongoDB server

## Installation

```bash
pip install spschedule
```

or

```bash
pip install -e "git+http://github.com/stylepage/spschedule.git#egg=spschedule"
```

or

```bash
git clone git@github.com:stylepage/spschedule.git spschedule
pip install -e spschedule
```

## Examples

```python
import spschedule

@spschedule.minutely()
def foo():
  print 'foo'

@spschedule.daily()
def bar():
  print 'bar'
  
spschedule.loop()
```


