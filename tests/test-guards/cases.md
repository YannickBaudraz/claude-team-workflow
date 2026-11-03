# What the test guards list

The cases `test_guards.py` runs through `skills/ask-team/scripts/test-guards.py`. Each case is a `##` heading, then one or more files. A file is a `File:` line with its path, a `Before:` block on the base branch and an `After:` block on the pull request's branch; `(none)` stands for a file that does not exist on that side. Then a `Listed:` line per change the guards list, as its key and its kind, or one `Listed: nothing`.

The cases live in this Markdown file, not in a code file, so the guards never read their examples as this repo's own tests.

## A deleted pytest test is listed

File: tests/test_cart.py
Before:
```
def test_add():
    assert True


def test_remove():
    assert True
```
After:
```
def test_add():
    assert True
```
Listed: tests/test_cart.py::test_remove deleted

## A test moved to another file is not listed

File: tests/test_cart.py
Before:
```
def test_add():
    assert True


def test_remove():
    assert True
```
After:
```
def test_add():
    assert True
```
File: tests/test_removal.py
Before:
(none)
After:
```
def test_remove():
    assert True
```
Listed: nothing

## A test whose name another file adds with a different body is listed

File: src/Button.test.tsx
Before:
```
it("renders", () => {
  render(button);
});
it("clicks", () => {
  render(button);
  expect(onClick).toHaveBeenCalled();
});
```
After:
```
it("renders", () => {
  render(button);
});
```
File: src/Other.test.ts
Before:
(none)
After:
```
it("clicks", () => {});
```
Listed: src/Button.test.tsx::clicks deleted

## One added test stands for one removed test of its name

File: src/menu.test.ts
Before:
```
describe("open", () => {
  it("renders", () => {
    expect(open()).toBe(true);
  });
});
describe("closed", () => {
  it("renders", () => {
    expect(open()).toBe(false);
  });
});
```
After:
```
describe("open", () => {
  it("renders", () => {
    expect(open()).toBe(true);
  });
});
```
Listed: src/menu.test.ts::renders deleted

## A test whose signature changes is not listed

File: tests/test_cart.py
Before:
```
def test_add():
    assert True
```
After:
```
def test_add(tmp_path):
    assert tmp_path
```
Listed: nothing

## A renamed test is listed under its old name

File: tests/test_cart.py
Before:
```
def test_add():
    assert True
```
After:
```
def test_adds_one_item():
    assert True
```
Listed: tests/test_cart.py::test_add deleted

## A test file deleted whole is listed once, as the file

File: tests/test_cart.py
Before:
```
def test_add():
    assert True


def test_remove():
    assert True
```
After:
(none)
Listed: tests/test_cart.py deleted

## A test file deleted whole whose tests all move is not listed

File: tests/test_cart.py
Before:
```
def test_add():
    assert True
```
After:
(none)
File: tests/test_basket.py
Before:
(none)
After:
```
def test_add():
    assert True
```
Listed: nothing

## A test file renamed so it is no longer a test file is listed once, as the file

File: tests/test_cart.py
Before:
```
def test_add():
    assert add(1, 2) == 3


def test_remove():
    assert remove(3, 1) == 2
```
After:
(none)
File: tests/test_cart.py.disabled
Before:
(none)
After:
```
def test_add():
    assert add(1, 2) == 3


def test_remove():
    assert remove(3, 1) == 2
```
Listed: tests/test_cart.py deleted

## A test file moved out of the test folder with an edit is listed once, as the file

File: tests/test_big.py
Before:
```
def test_sum():
    assert total([1, 2, 3]) == 6


def test_empty():
    assert total([]) == 0


def test_negative():
    assert total([-1, 1]) == 0
```
After:
(none)
File: lib/big_checks.py
Before:
(none)
After:
```
def test_sum():
    assert total([1, 2, 3]) == 6


def test_empty():
    assert total([]) == 0


def test_negative():
    assert total([-2, 2]) == 0
```
Listed: tests/test_big.py deleted

## A JavaScript test file renamed to a backup is listed once, as the file

File: src/cart.test.ts
Before:
```
it("adds", () => {
  expect(add(1, 2)).toBe(3);
});

it("removes", () => {
  expect(remove(3, 1)).toBe(2);
});
```
After:
(none)
File: src/cart.ts.orig
Before:
(none)
After:
```
it("adds", () => {
  expect(add(1, 2)).toBe(3);
});

it("removes", () => {
  expect(remove(3, 1)).toBe(2);
});
```
Listed: src/cart.test.ts deleted

## A test file renamed to another test file is not listed

File: tests/test_cart.py
Before:
```
def test_add():
    assert add(1, 2) == 3


def test_remove():
    assert remove(3, 1) == 2
```
After:
(none)
File: tests/test_basket.py
Before:
(none)
After:
```
def test_add():
    assert add(1, 2) == 3


def test_remove():
    assert remove(3, 1) == 2
```
Listed: nothing

## A helper file deleted from a test folder is not listed

File: tests/conftest.py
Before:
```
import pytest
```
After:
(none)
Listed: nothing

## A test removed from a source file that is not a test file is not listed

File: src/cart.py
Before:
```
def test_mode():
    return False
```
After:
```
def mode():
    return False
```
Listed: nothing

## A pytest skip marker names the test below it

File: tests/test_cart.py
Before:
```
def test_total():
    assert True
```
After:
```
import pytest


@pytest.mark.skip(reason="flaky")
def test_total():
    assert True
```
Listed: tests/test_cart.py::test_total newly skipped

## A skip inside a unittest test names that test

File: tests/test_cart.py
Before:
```
import unittest


class CartTest(unittest.TestCase):
    def test_total(self):
        self.assertTrue(True)
```
After:
```
import unittest


class CartTest(unittest.TestCase):
    def test_total(self):
        self.skipTest("waits on the new prices")
        self.assertTrue(True)
```
Listed: tests/test_cart.py::test_total newly skipped

## A skip on a class names the class

File: tests/test_cart.py
Before:
```
import unittest


class CartTest(unittest.TestCase):
    def test_total(self):
        self.assertTrue(True)
```
After:
```
import unittest


@unittest.skip("being rewritten")
class CartTest(unittest.TestCase):
    def test_total(self):
        self.assertTrue(True)
```
Listed: tests/test_cart.py::CartTest newly skipped

## A skip for the whole module names the file

File: tests/test_cart.py
Before:
```
import pytest


def test_total():
    assert True
```
After:
```
import pytest

pytestmark = pytest.mark.skip(reason="slow")


def test_total():
    assert True
```
Listed: tests/test_cart.py newly skipped

## A skip that only moves is not listed

File: tests/test_cart.py
Before:
```
import pytest


def test_add():
    assert True


@pytest.mark.skip(reason="needs a network")
def test_sync():
    assert True
```
After:
```
import pytest


@pytest.mark.skip(reason="needs a network")
def test_sync():
    assert True


def test_add():
    assert True
```
Listed: nothing

## An xfail counts as a skip

File: tests/test_cart.py
Before:
```
def test_total():
    assert True
```
After:
```
import pytest


@pytest.mark.xfail
def test_total():
    assert True
```
Listed: tests/test_cart.py::test_total newly skipped

## A JavaScript it.skip names its test

File: src/cart.test.ts
Before:
```
describe("cart", () => {
  it("adds an item", () => {
    expect(1).toBe(1);
  });
});
```
After:
```
describe("cart", () => {
  it.skip("adds an item", () => {
    expect(1).toBe(1);
  });
});
```
Listed: src/cart.test.ts::adds an item newly skipped

## A JavaScript xit names its test, and xdescribe its group

File: src/cart.spec.js
Before:
```
describe("cart", () => {
  it("adds an item", () => {});
});
describe("totals", () => {
  it("sums", () => {});
});
```
After:
```
describe("cart", () => {
  xit("adds an item", () => {});
});
xdescribe("totals", () => {
  it("sums", () => {});
});
```
Listed: src/cart.spec.js::adds an item newly skipped
Listed: src/cart.spec.js::totals newly skipped

## A deleted JavaScript test is listed by its name

File: __tests__/cart.js
Before:
```
test("adds an item", () => {});
test("removes an item", () => {});
```
After:
```
test("adds an item", () => {});
```
Listed: __tests__/cart.js::removes an item deleted

## A JavaScript test commented out is listed as deleted

File: src/B.test.ts
Before:
```
it("loads", () => {
  expect(load()).toBe(1);
});
it("renders", () => {
  expect(render()).toBe(1);
});
```
After:
```
it("loads", () => {
  expect(load()).toBe(1);
});
// it("renders", () => {
//   expect(render()).toBe(1);
// });
```
Listed: src/B.test.ts::renders deleted

## A skip written in a comment is not listed

File: src/cart.test.ts
Before:
```
it("adds an item", () => {});
```
After:
```
// Use it.skip("...") while the price service is down.
it("adds an item", () => {});
```
Listed: nothing

## A Go skip names the test around it

File: cart/cart_test.go
Before:
```
package cart

import "testing"

func TestTotal(t *testing.T) {
	if Total() != 0 {
		t.Fatal("not zero")
	}
}
```
After:
```
package cart

import "testing"

func TestTotal(t *testing.T) {
	t.Skip("prices change next week")
	if Total() != 0 {
		t.Fatal("not zero")
	}
}
```
Listed: cart/cart_test.go::TestTotal newly skipped

## A deleted Go test is listed

File: cart/cart_test.go
Before:
```
package cart

import "testing"

func TestAdd(t *testing.T) {}

func TestRemove(t *testing.T) {}
```
After:
```
package cart

import "testing"

func TestAdd(t *testing.T) {}
```
Listed: cart/cart_test.go::TestRemove deleted

## A Java @Disabled names the method below its annotations

File: src/test/java/shop/CartTest.java
Before:
```
class CartTest {
    @Test
    void addsAnItem() {
    }
}
```
After:
```
class CartTest {
    @Disabled("flaky on CI")
    @Test
    void addsAnItem() {
    }
}
```
Listed: src/test/java/shop/CartTest.java::addsAnItem newly skipped

## A deleted Java test is listed by its method

File: src/test/java/shop/CartTest.java
Before:
```
class CartTest {
    @Test
    void addsAnItem() {
    }

    @Test
    public void removesAnItem() {
    }
}
```
After:
```
class CartTest {
    @Test
    void addsAnItem() {
    }
}
```
Listed: src/test/java/shop/CartTest.java::removesAnItem deleted

## An xUnit Skip names its method

File: tests/Shop.Tests/CartTests.cs
Before:
```
public class CartTests
{
    [Fact]
    public void AddsAnItem()
    {
    }
}
```
After:
```
public class CartTests
{
    [Fact(Skip = "flaky")]
    public void AddsAnItem()
    {
    }
}
```
Listed: tests/Shop.Tests/CartTests.cs::AddsAnItem newly skipped

## A Rust #[ignore] in a source file names its test

File: src/cart.rs
Before:
```
#[cfg(test)]
mod tests {
    #[test]
    fn adds_an_item() {}
}
```
After:
```
#[cfg(test)]
mod tests {
    #[test]
    #[ignore]
    fn adds_an_item() {}
}
```
Listed: src/cart.rs::adds_an_item newly skipped

## A deleted Rust test in a source file is listed

File: src/cart.rs
Before:
```
pub fn total() -> u32 {
    0
}

#[cfg(test)]
mod tests {
    #[test]
    fn adds_an_item() {}

    #[test]
    fn removes_an_item() {}
}
```
After:
```
pub fn total() -> u32 {
    0
}

#[cfg(test)]
mod tests {
    #[test]
    fn adds_an_item() {}
}
```
Listed: src/cart.rs::removes_an_item deleted

## A Rust test whose #[test] alone is removed is listed

File: src/cart.rs
Before:
```
#[cfg(test)]
mod tests {
    #[test]
    fn adds_an_item() {}
}
```
After:
```
#[cfg(test)]
mod tests {
    fn adds_an_item() {}
}
```
Listed: src/cart.rs::adds_an_item deleted

## A Rust #[test] that becomes #[tokio::test] is not listed

File: src/cart.rs
Before:
```
#[cfg(test)]
mod tests {
    #[test]
    fn adds_an_item() {}
}
```
After:
```
#[cfg(test)]
mod tests {
    #[tokio::test]
    fn adds_an_item() {}
}
```
Listed: nothing

## A Java @Test commented out is listed as deleted

File: src/test/java/shop/CartTest.java
Before:
```
class CartTest {
    @Test
    void addsAnItem() {
    }
}
```
After:
```
class CartTest {
    // @Test
    void addsAnItem() {
    }
}
```
Listed: src/test/java/shop/CartTest.java::addsAnItem deleted

## A Java test renamed under the same @Test is listed under its old name

File: src/test/java/shop/CartTest.java
Before:
```
class CartTest {
    @Test
    void addsAnItem() {
        assertTrue(true);
    }
}
```
After:
```
class CartTest {
    @Test
    void addsOneItem() {
        assertTrue(true);
    }
}
```
Listed: src/test/java/shop/CartTest.java::addsAnItem deleted

## A deleted xUnit test is listed by its method

File: tests/Shop.Tests/CartTests.cs
Before:
```
public class CartTests
{
    [Fact]
    public void AddsAnItem()
    {
    }

    [Fact]
    public void RemovesAnItem()
    {
    }
}
```
After:
```
public class CartTests
{
    [Fact]
    public void AddsAnItem()
    {
    }
}
```
Listed: tests/Shop.Tests/CartTests.cs::RemovesAnItem deleted

## A PHPUnit deletion and markTestSkipped are both listed

File: tests/CartTest.php
Before:
```
<?php
final class CartTest extends TestCase
{
    /** @test */
    public function it_adds_an_item(): void
    {
        $this->assertTrue(true);
    }

    public function testRemovesAnItem(): void
    {
        $this->assertTrue(true);
    }
}
```
After:
```
<?php
final class CartTest extends TestCase
{
    /** @test */
    public function it_adds_an_item(): void
    {
        $this->markTestSkipped('waits on the price service');
        $this->assertTrue(true);
    }
}
```
Listed: tests/CartTest.php::testRemovesAnItem deleted
Listed: tests/CartTest.php::it_adds_an_item newly skipped

## A Swift deletion and XCTSkip are both listed

File: Tests/ShopTests/CartTests.swift
Before:
```
final class CartTests: XCTestCase {
    func testAddsAnItem() throws {
        XCTAssertTrue(true)
    }

    func testRemovesAnItem() throws {
        XCTAssertTrue(true)
    }
}
```
After:
```
final class CartTests: XCTestCase {
    func testAddsAnItem() throws {
        throw XCTSkip("waits on the price service")
    }
}
```
Listed: Tests/ShopTests/CartTests.swift::testRemovesAnItem deleted
Listed: Tests/ShopTests/CartTests.swift::testAddsAnItem newly skipped

## An Elixir deletion and @tag :skip are both listed

File: test/cart_test.exs
Before:
```
defmodule CartTest do
  use ExUnit.Case

  test "adds an item" do
    assert true
  end

  test "removes an item" do
    assert true
  end
end
```
After:
```
defmodule CartTest do
  use ExUnit.Case

  @tag :skip
  test "adds an item" do
    assert true
  end
end
```
Listed: test/cart_test.exs::removes an item deleted
Listed: test/cart_test.exs::adds an item newly skipped

## A Dart test commented out and a skip are both listed

File: test/cart_test.dart
Before:
```
void main() {
  test('adds an item', () {
    expect(1, 1);
  });

  test('removes an item', () {
    expect(1, 1);
  });
}
```
After:
```
void main() {
  test('adds an item', () {
    expect(1, 1);
  }, skip: 'waits on the price service');

  // test('removes an item', () {
  //   expect(1, 1);
  // });
}
```
Listed: test/cart_test.dart::removes an item deleted
Listed: test/cart_test.dart::adds an item newly skipped

## A Ruby skip names the example around it

File: spec/cart_spec.rb
Before:
```
describe Cart do
  it "adds an item" do
    expect(1).to eq(1)
  end
end
```
After:
```
describe Cart do
  it "adds an item" do
    skip "waits on the new prices"
    expect(1).to eq(1)
  end
end
```
Listed: spec/cart_spec.rb::adds an item newly skipped

## Skip words in a file that is not a test are not listed

File: src/cart.py
Before:
```
def total():
    return 0
```
After:
```
import pytest


def total():
    pytest.skip("not a test file")
    return 0
```
Listed: nothing

## A pattern from --tests makes a file a test file

Arguments: --tests checks/*.py
File: checks/cart.py
Before:
```
def test_add():
    assert True


def test_remove():
    assert True
```
After:
```
def test_add():
    assert True
```
Listed: checks/cart.py::test_remove deleted

## A deletion and a skip in one change are both listed

File: tests/test_cart.py
Before:
```
def test_add():
    pass


def test_remove():
    pass
```
After:
```
import pytest


def test_add():
    pytest.skip("later")
```
Listed: tests/test_cart.py::test_remove deleted
Listed: tests/test_cart.py::test_add newly skipped
