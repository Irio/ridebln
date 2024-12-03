def did_it_book(driver):
    return (
        "You have been successfully enrolled in the class highlighted below"
        in driver.page_source
    )
