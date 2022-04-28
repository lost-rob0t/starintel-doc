
# Table of Contents

1.  [Star Intel Document Spec](#orgfc60b35)
2.  [Star Intel Document](#orgb40bcfe)
    1.  [BookerDocument Examples](#org6e67c14)
        1.  [Create documents](#org626adc7)



<a id="orgfc60b35"></a>

# Star Intel Document Spec

This python package defines python dataclasses so your project will be abled to create valid Starintel documents

Starintel is a WIP framework to allow a osint operator to collect and add metadata to information. weather it is from message bots or data breaches it is up to you to get it there.
Once you have the data you will be abled to explore it or search it with a WIP web app. cli/api is on the roadmap.

The documents are stored in Apache Couchdb version 3.


<a id="orgb40bcfe"></a>

# Star Intel Document

You can read the documentation [[][here]]


<a id="org6e67c14"></a>

## BookerDocument Examples

For example lets say you have json file containing the following

    {"fname": "joe",
     "lname": "biden",
     "address": "1600 Pennsylvania Ave NW Washington, DC 20500"}


<a id="org626adc7"></a>

### Create documents

    from starintel_doc import BookerAddress, BookerPerson, make_id
    import json
    import address_magic
    data = {"fname": "joe",
            "lname": "biden",
            "age": 79
            "address": "1600 Pennsylvania Ave NW Washington, DC 20500"}

    # Create a person
    person = BookerPerson(fname=data["fname"], lname=data["biden"],
                          age=data["age"])
    # make sha256 id
    person._id = make_id(person.fname + person.lname)
    a = Address(data["address"])
    # Check if address seems valid
    if a.validate(need_postal=True):
        street = f"{a.house_number} {a.road} {a.city} {a.state}, {a.postcode}"
        address = BookerAddress(street=street, city=a.city, state=a.state, zip=a.postcode)
        # make sha256 id
        address._id = make_id(address.street + address.city + address.state + address.zip)


    # Create a reference of the address to the person
    person.address.append(address._id)

    # Create a reference of the person to the address
    address.members.append(person._id)

    print(person.make_doc())
    print(address.make_doc())
