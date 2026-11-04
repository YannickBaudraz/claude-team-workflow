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
Listed: tests/test_cart.py::CartTest::test_total newly skipped

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
Listed: src/cart.test.ts::cart::adds an item newly skipped

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
Listed: src/cart.spec.js::cart::adds an item newly skipped
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
Listed: src/test/java/shop/CartTest.java::CartTest::addsAnItem newly skipped

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
Listed: Tests/ShopTests/CartTests.swift::CartTests::testAddsAnItem newly skipped

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
Listed: spec/cart_spec.rb::Cart::adds an item newly skipped

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

## A .gitattributes line that shows tests as binary hides nothing

File: .gitattributes
Before:
(none)
After:
```
tests/** -diff
```
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
import pytest


@pytest.mark.skip(reason="later")
def test_add():
    assert True
```
File: tests/test_other.py
Before:
```
def test_other():
    assert True
```
After:
(none)
Listed: tests/test_cart.py::test_remove deleted
Listed: tests/test_cart.py::test_add newly skipped
Listed: tests/test_other.py deleted

## A JavaScript test wrapped in a block comment is listed as deleted

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
```
it("adds", () => {
  expect(add(1, 2)).toBe(3);
});
/*
it("removes", () => {
  expect(remove(3, 1)).toBe(2);
});
*/
```
Listed: src/cart.test.ts::removes deleted

## A Python test wrapped in a triple-quoted string is listed as deleted

File: tests/test_cart.py
Before:
```
def test_add():
    assert add(1, 2) == 3


def test_remove():
    assert remove(3, 1) == 2
```
After:
```
def test_add():
    assert add(1, 2) == 3


"""
def test_remove():
    assert remove(3, 1) == 2
"""
```
Listed: tests/test_cart.py::test_remove deleted

## A Java test in a block comment that comes back is not listed, and a skip in one is not a skip

File: src/test/java/CartTest.java
Before:
```
class CartTest {
    /*
    @Test
    void removes() {}
    */

    @Test
    void adds() {}
}
```
After:
```
class CartTest {
    @Test
    void removes() {}

    /* @Disabled("later") */
    @Test
    void adds() {}
}
```
Listed: nothing

## A skip taken off one test and put on another is listed

File: tests/test_cart.py
Before:
```
import pytest


@pytest.mark.skip(reason="flaky")
def test_a():
    assert True


def test_b():
    assert True
```
After:
```
import pytest


def test_a():
    assert True


@pytest.mark.skip(reason="flaky")
def test_b():
    assert True
```
Listed: tests/test_cart.py::test_b newly skipped

## A skip word inside a test's name is not a skip

File: src/parser.test.ts
Before:
```
it("parses", () => {});
```
After:
```
it("parses", () => {});
it("reads it.skip in a spec", () => {});
```
Listed: nothing

## A test deleted from Django's tests.py is listed

File: shop/tests.py
Before:
```
class CartTests(TestCase):
    def test_add(self):
        self.assertTrue(True)

    def test_remove(self):
        self.assertTrue(True)
```
After:
```
class CartTests(TestCase):
    def test_add(self):
        self.assertTrue(True)
```
Listed: shop/tests.py::test_remove deleted

## A test deleted from a Cypress spec is listed

File: cypress/e2e/cart.cy.ts
Before:
```
it("adds", () => {});
it("removes", () => {});
```
After:
```
it("adds", () => {});
```
Listed: cypress/e2e/cart.cy.ts::removes deleted

## A deleted it.each test is listed

File: src/sum.test.ts
Before:
```
it.each([[1, 2, 3]])("adds %i and %i", (a, b, sum) => {
  expect(a + b).toBe(sum);
});
test.each(cases)("subtracts %i", (a) => {
  expect(a - a).toBe(0);
});
```
After:
```
test.each(cases)("subtracts %i", (a) => {
  expect(a - a).toBe(0);
});
```
Listed: src/sum.test.ts::adds %i and %i deleted

## A Vitest skipIf names its test, and is not read as a deletion

File: src/cart.test.ts
Before:
```
it("adds", () => {});
```
After:
```
it.skipIf(process.env.CI)("adds", () => {});
```
Listed: src/cart.test.ts::adds newly skipped

## A Playwright test.describe.skip names its group

File: e2e/cart.spec.ts
Before:
```
test.describe("cart", () => {
  test("adds", async ({ page }) => {});
});
```
After:
```
test.describe.skip("cart", () => {
  test("adds", async ({ page }) => {});
});
```
Listed: e2e/cart.spec.ts::cart newly skipped

## A pytest mark imported by name still skips

File: tests/test_cart.py
Before:
```
from pytest import mark


def test_add():
    assert True
```
After:
```
from pytest import mark


@mark.skip(reason="later")
def test_add():
    assert True
```
Listed: tests/test_cart.py::test_add newly skipped

## An RSpec skip given as metadata is listed

File: spec/cart_spec.rb
Before:
```
describe Cart do
  it "adds an item" do
    expect(1).to eq(1)
  end

  it "removes an item" do
    expect(1).to eq(1)
  end
end
```
After:
```
describe Cart do
  it "adds an item", skip: "later" do
    expect(1).to eq(1)
  end

  it "removes an item", :skip do
    expect(1).to eq(1)
  end
end
```
Listed: spec/cart_spec.rb::Cart::adds an item newly skipped
Listed: spec/cart_spec.rb::Cart::removes an item newly skipped

## An NUnit Ignore inside the Test attribute is listed

File: tests/CartTests.cs
Before:
```
public class CartTests
{
    [Test]
    public void Adds()
    {
    }
}
```
After:
```
public class CartTests
{
    [Test, Ignore("waits on prices")]
    public void Adds()
    {
    }
}
```
Listed: tests/CartTests.cs::Adds newly skipped

## A TestNG test turned off with enabled = false is listed

File: src/test/java/CartTest.java
Before:
```
public class CartTest {
    @Test
    public void adds() {
    }
}
```
After:
```
public class CartTest {
    @Test(enabled = false)
    public void adds() {
    }
}
```
Listed: src/test/java/CartTest.java::CartTest::adds newly skipped

## A Go Skip on something other than a test is not a skip

File: xml/parse_test.go
Before:
```
func TestParse(t *testing.T) {
	d := xml.NewDecoder(r)
	d.Token()
}
```
After:
```
func TestParse(t *testing.T) {
	d := xml.NewDecoder(r)
	d.Skip()
}
```
Listed: nothing

## A testify suite's Skip is listed

File: cart/cart_test.go
Before:
```
func (s *CartSuite) TestAdds() {
	s.Equal(1, 1)
}
```
After:
```
func (s *CartSuite) TestAdds() {
	s.T().Skip("later")
	s.Equal(1, 1)
}
```
Listed: cart/cart_test.go::TestAdds newly skipped

## SwiftUI's disabled modifier is not a skip, a Swift Testing trait is

File: Tests/ShopTests/CartViewTests.swift
Before:
```
final class CartViewTests: XCTestCase {
    func testRenders() {
        let view = Button("Pay") {}
        XCTAssertNotNil(view)
    }
}

@Test func adds() {
}
```
After:
```
final class CartViewTests: XCTestCase {
    func testRenders() {
        let view = Button("Pay") {}.disabled(true)
        XCTAssertNotNil(view)
    }
}

@Test(.disabled("later")) func adds() {
}
```
Listed: Tests/ShopTests/CartViewTests.swift::adds newly skipped

## A test file that is a test only by its folder, renamed out of it, is listed once, as the file

File: __tests__/cart.js
Before:
```
test("adds an item", () => {
  expect(add(1, 2)).toBe(3);
});
test("removes an item", () => {
  expect(remove(3, 1)).toBe(2);
});
```
After:
(none)
File: src/cart_old.js
Before:
(none)
After:
```
test("adds an item", () => {
  expect(add(1, 2)).toBe(3);
});
test("removes an item", () => {
  expect(remove(3, 1)).toBe(2);
});
```
Listed: __tests__/cart.js deleted

## A change to a file named with --guard is listed

Arguments: --guard ci/guards.py
File: ci/guards.py
Before:
```
CHECK = True
```
After:
```
CHECK = False
```
Listed: ci/guards.py changed

## A JavaScript regex that holds slash-star hides no test below it

File: src/cart.test.js
Before:
```
const trim = (u) => u.replace(/\/*$/, "");

it("adds", () => {
  expect(trim("a/")).toBe("a");
});

it("removes", () => {
  expect(2).toBe(2);
});
```
After:
```
const trim = (u) => u.replace(/\/*$/, "");

it.skip("adds", () => {
  expect(trim("a/")).toBe("a");
});
```
Listed: src/cart.test.js::removes deleted
Listed: src/cart.test.js::adds newly skipped

## A JavaScript regex that holds a backtick hides no test below it

File: src/quote.test.js
Before:
```
const tick = /`/;

it("adds", () => {
  expect(tick.test("`")).toBe(true);
});

it("removes", () => {
  expect(2).toBe(2);
});
```
After:
```
const tick = /`/;

it.skip("adds", () => {
  expect(tick.test("`")).toBe(true);
});
```
Listed: src/quote.test.js::removes deleted
Listed: src/quote.test.js::adds newly skipped

## A division in JavaScript is not read as a regex

File: src/ratio.test.js
Before:
```
const half = total / 2; // a/b
it("adds", () => {
  expect(half / 1).toBe(half);
});
it("removes", () => {});
```
After:
```
const half = total / 2; // a/b
it("adds", () => {
  expect(half / 1).toBe(half);
});
```
Listed: src/ratio.test.js::removes deleted

## A multi-line skipif moved onto another test is listed

File: tests/test_cart.py
Before:
```
import sys

import pytest


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="flaky",
)
def test_add():
    assert True


def test_total():
    assert True
```
After:
```
import sys

import pytest


def test_add():
    assert True


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="flaky",
)
def test_total():
    assert True
```
Listed: tests/test_cart.py::test_total newly skipped

## A multi-line skipif moved onto another test in a class is listed

File: tests/test_cart.py
Before:
```
import sys

import pytest


class TestCart:
    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="flaky",
    )
    def test_add(self):
        assert True

    def test_total(self):
        assert True
```
After:
```
import sys

import pytest


class TestCart:
    def test_add(self):
        assert True

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="flaky",
    )
    def test_total(self):
        assert True
```
Listed: tests/test_cart.py::TestCart::test_total newly skipped

## A new multi-line skipif names its test

File: tests/test_cart.py
Before:
```
import sys

import pytest


def test_add():
    assert True
```
After:
```
import sys

import pytest


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="flaky (see #12)",
)
def test_add():
    assert True
```
Listed: tests/test_cart.py::test_add newly skipped

## A Swift Testing disabled trait on a wrapped trait list is listed

File: Tests/CartTests.swift
Before:
```
import Testing

@Test("adds", .tags(.cart))
func adds() {
    #expect(true)
}
```
After:
```
import Testing

@Test("adds", .tags(.cart),
      .disabled("flaky on CI"))
func adds() {
    #expect(true)
}
```
Listed: Tests/CartTests.swift::adds newly skipped

## SwiftUI's disabled modifier inside a test suite's body is not a skip

File: Tests/CartViewTests.swift
Before:
```
import Testing

@Suite(.serialized) struct CartViewTests {
    @Test func renders() {
        let view = Button("Pay") {}
        #expect(view != nil)
    }
}
```
After:
```
import Testing

@Suite(.serialized) struct CartViewTests {
    @Test func renders() {
        let view = Button("Pay") {}
            .disabled(true)
        #expect(view != nil)
    }
}
```
Listed: nothing

## A pytestmark list over several lines skips the whole file

File: tests/test_cart.py
Before:
```
import pytest


def test_add():
    assert True
```
After:
```
import pytest

pytestmark = [
    pytest.mark.skip(reason="later"),
]


def test_add():
    assert True
```
Listed: tests/test_cart.py newly skipped

## A skip given to one case of a parametrize names its test

File: tests/test_cart.py
Before:
```
import pytest


def test_add():
    assert True


@pytest.mark.parametrize(
    "x",
    [1, 2],
)
def test_total(x):
    assert x
```
After:
```
import pytest


def test_add():
    assert True


@pytest.mark.parametrize(
    "x",
    [1, pytest.param(2, marks=pytest.mark.skip)],
)
def test_total(x):
    assert x
```
Listed: tests/test_cart.py::test_total newly skipped

## Mocha's this.skip names its test

File: test/cart.spec.js
Before:
```
it("adds", function () {
  expect(1).to.equal(1);
});
```
After:
```
it("adds", function () {
  this.skip();
  expect(1).to.equal(1);
});
```
Listed: test/cart.spec.js::adds newly skipped

## A JavaScript it.only lists its file, whose other tests stop running

File: src/cart.test.js
Before:
```
it("adds", () => {
  expect(add()).toBe(1);
});

it("removes", () => {
  expect(remove()).toBe(0);
});
```
After:
```
it.only("adds", () => {
  expect(add()).toBe(1);
});

it("removes", () => {
  expect(remove()).toBe(0);
});
```
Listed: src/cart.test.js newly skipped

## A describe.only lists its file

File: src/cart.test.ts
Before:
```
describe("cart", () => {
  it("adds", () => {});
});

describe("order", () => {
  it("pays", () => {});
});
```
After:
```
describe.only("cart", () => {
  it("adds", () => {});
});

describe("order", () => {
  it("pays", () => {});
});
```
Listed: src/cart.test.ts newly skipped

## A Jasmine fit lists its file and is not read as a deletion

File: spec/cart.spec.js
Before:
```
describe("cart", () => {
  it("adds", () => {
    expect(add()).toBe(1);
  });

  it("removes", () => {
    expect(remove()).toBe(0);
  });
});
```
After:
```
describe("cart", () => {
  fit("adds", () => {
    expect(add()).toBe(1);
  });

  it("removes", () => {
    expect(remove()).toBe(0);
  });
});
```
Listed: spec/cart.spec.js newly skipped

## A test moved into a describe.skip that was already there is listed

File: src/cart.test.js
Before:
```
describe.skip("legacy", () => {
  it("old path", () => {
    expect(old()).toBe(1);
  });
});

describe("cart", () => {
  it("adds", () => {
    expect(add()).toBe(1);
  });
});
```
After:
```
describe.skip("legacy", () => {
  it("old path", () => {
    expect(old()).toBe(1);
  });

  it("adds", () => {
    expect(add()).toBe(1);
  });
});

describe("cart", () => {
});
```
Listed: src/cart.test.js::legacy::adds newly skipped

## A test moved into a skipped pytest class that was already there is listed

File: tests/test_cart.py
Before:
```
import pytest


@pytest.mark.skip(reason="legacy")
class TestLegacy:
    def test_old(self):
        assert old() == 1


class TestCart:
    def test_add(self):
        assert add() == 1
```
After:
```
import pytest


@pytest.mark.skip(reason="legacy")
class TestLegacy:
    def test_old(self):
        assert old() == 1

    def test_add(self):
        assert add() == 1


class TestCart:
    pass
```
Listed: tests/test_cart.py::TestLegacy::test_add newly skipped

## A test moved into a file skipped whole is listed

File: tests/test_cart.py
Before:
```
def test_add():
    assert add() == 1


def test_keep():
    assert keep()
```
After:
```
def test_keep():
    assert keep()
```
File: tests/test_legacy.py
Before:
```
import pytest

pytestmark = pytest.mark.skip(reason="legacy")


def test_old():
    assert old() == 1
```
After:
```
import pytest

pytestmark = pytest.mark.skip(reason="legacy")


def test_old():
    assert old() == 1


def test_add():
    assert add() == 1
```
Listed: tests/test_legacy.py::test_add newly skipped

## A test edited inside a group skipped before is not listed

File: src/legacy.test.js
Before:
```
describe.skip("legacy", () => {
  it("old path", () => {
    expect(old()).toBe(1);
  });
});
```
After:
```
describe.skip("legacy", () => {
  it("old path", () => {
    expect(old()).toBe(2);
  });
});
```
Listed: nothing

## A pytest skip moved to a test of the same name in another class is listed

File: tests/test_shop.py
Before:
```
import pytest


class TestCart:
    @pytest.mark.skip(reason="flaky")
    def test_empty(self):
        assert cart() == []


class TestOrder:
    def test_empty(self):
        assert order() == []
```
After:
```
import pytest


class TestCart:
    def test_empty(self):
        assert cart() == []


class TestOrder:
    @pytest.mark.skip(reason="flaky")
    def test_empty(self):
        assert order() == []
```
Listed: tests/test_shop.py::TestOrder::test_empty newly skipped

## An it.skip moved to a test of the same name in another describe is listed

File: src/shop.test.js
Before:
```
describe("cart", () => {
  it.skip("is empty", () => {
    expect(cart()).toEqual([]);
  });
});

describe("order", () => {
  it("is empty", () => {
    expect(order()).toEqual([]);
  });
});
```
After:
```
describe("cart", () => {
  it("is empty", () => {
    expect(cart()).toEqual([]);
  });
});

describe("order", () => {
  it.skip("is empty", () => {
    expect(order()).toEqual([]);
  });
});
```
Listed: src/shop.test.js::order::is empty newly skipped

## A pytest file renamed in its test folder to a name pytest does not collect is listed

File: tests/test_cart.py
Before:
```
def test_add():
    assert add() == 1


def test_remove():
    assert remove() == 0
```
After:
(none)
File: tests/cart_checks.py
Before:
(none)
After:
```
def test_add():
    assert add() == 1


def test_remove():
    assert remove() == 0
```
Listed: tests/test_cart.py deleted

## A Go test file renamed off _test.go is listed, even in a test folder

File: test/cart_test.go
Before:
```
package cart

import "testing"

func TestAdd(t *testing.T) {
	if Add() != 1 {
		t.Fatal("x")
	}
}
```
After:
(none)
File: test/cart_tests.go
Before:
(none)
After:
```
package cart

import "testing"

func TestAdd(t *testing.T) {
	if Add() != 1 {
		t.Fatal("x")
	}
}
```
Listed: test/cart_test.go deleted

## A JavaScript test file renamed off its .test suffix in a test folder is listed

File: test/cart.test.js
Before:
```
it("adds", () => {
  expect(add()).toBe(1);
});
```
After:
(none)
File: test/cart.js
Before:
(none)
After:
```
it("adds", () => {
  expect(add()).toBe(1);
});
```
Listed: test/cart.test.js deleted

## A test moved from a test file into a helper of its test folder is listed

File: tests/test_cart.py
Before:
```
def test_add():
    assert add() == 1
```
After:
(none)
File: tests/helpers.py
Before:
(none)
After:
```
def helper_0(cart):
    return cart.items[0]


def helper_1(cart):
    return cart.items[1]


def helper_2(cart):
    return cart.items[2]


def helper_3(cart):
    return cart.items[3]


def helper_4(cart):
    return cart.items[4]


def helper_5(cart):
    return cart.items[5]


def helper_6(cart):
    return cart.items[6]


def helper_7(cart):
    return cart.items[7]


def helper_8(cart):
    return cart.items[8]


def helper_9(cart):
    return cart.items[9]


def helper_10(cart):
    return cart.items[10]


def helper_11(cart):
    return cart.items[11]


def test_add():
    assert add() == 1
```
Listed: tests/test_cart.py deleted

## A deleted Swift Testing test in a SwiftPM test target is listed

File: Tests/AppTests/Cart.swift
Before:
```
import Testing

@Test func adds() {
    #expect(add() == 1)
}

@Test func removes() {
    #expect(remove() == 0)
}
```
After:
```
import Testing

@Test func adds() {
    #expect(add() == 1)
}
```
Listed: Tests/AppTests/Cart.swift::removes deleted

## A deleted xUnit test in a .Tests project is listed

File: src/Shop.Tests/Cart.cs
Before:
```
public class Cart
{
    [Fact]
    public void Adds()
    {
        Assert.Equal(1, Add());
    }

    [Fact]
    public void Removes()
    {
        Assert.Equal(0, Remove());
    }
}
```
After:
```
public class Cart
{
    [Fact]
    public void Adds()
    {
        Assert.Equal(1, Add());
    }
}
```
Listed: src/Shop.Tests/Cart.cs::Removes deleted

## A pytest importorskip at the top of a file skips the whole file

File: tests/test_cart.py
Before:
```
import pytest


def test_add():
    assert add() == 1


def test_remove():
    assert remove() == 0
```
After:
```
import pytest

np = pytest.importorskip("nope")


def test_add():
    assert add() == 1


def test_remove():
    assert remove() == 0
```
Listed: tests/test_cart.py newly skipped

## A Go build constraint added to a test file is listed

File: cart/cart_test.go
Before:
```
package cart

import "testing"

func TestAdd(t *testing.T) {
	if Add() != 1 {
		t.Fatal("x")
	}
}
```
After:
```
//go:build ignore

package cart

import "testing"

func TestAdd(t *testing.T) {
	if Add() != 1 {
		t.Fatal("x")
	}
}
```
Listed: cart/cart_test.go newly skipped

## A pytest class renamed off its Test prefix is listed as its tests deleted

File: tests/test_cart.py
Before:
```
class TestCart:
    def test_add(self):
        assert add() == 1

    def test_remove(self):
        assert remove() == 0
```
After:
```
class Cart:
    def test_add(self):
        assert add() == 1

    def test_remove(self):
        assert remove() == 0
```
Listed: tests/test_cart.py::test_add deleted
Listed: tests/test_cart.py::test_remove deleted

## A JUnit assumption and @EnabledOnOs are listed

File: src/test/java/CartTest.java
Before:
```
class CartTest {
    @Test
    void adds() {
        assertEquals(1, add());
    }

    @Test
    void removes() {
        assertEquals(0, remove());
    }
}
```
After:
```
class CartTest {
    @Test
    void adds() {
        assumeTrue(System.getenv("PRICES") != null);
        assertEquals(1, add());
    }

    @Test
    @EnabledOnOs(OS.WINDOWS)
    void removes() {
        assertEquals(0, remove());
    }
}
```
Listed: src/test/java/CartTest.java::CartTest::adds newly skipped
Listed: src/test/java/CartTest.java::CartTest::removes newly skipped

## A new Go test in a file whose helper skips is not listed

File: cart_test.go
Before:
```
package cart

import "testing"

func requireDocker(t *testing.T) {
	if !docker() {
		t.Skip("no docker")
	}
}

func TestAdd(t *testing.T) {
	requireDocker(t)
}
```
After:
```
package cart

import "testing"

func requireDocker(t *testing.T) {
	if !docker() {
		t.Skip("no docker")
	}
}

func TestAdd(t *testing.T) {
	requireDocker(t)
}

func TestRemove(t *testing.T) {
	if Remove() != 0 {
		t.Fatal("x")
	}
}
```
Listed: nothing

## A new pytest test in a file whose fixture skips is not listed

File: tests/test_cart.py
Before:
```
import pytest


@pytest.fixture
def db():
    if not HAVE_DB:
        pytest.skip("no db")
    return connect()


def test_add(db):
    assert add(db) == 1
```
After:
```
import pytest


@pytest.fixture
def db():
    if not HAVE_DB:
        pytest.skip("no db")
    return connect()


def test_add(db):
    assert add(db) == 1


def test_total():
    assert total() == 0
```
Listed: nothing

## A skip added to a pytest fixture is listed under the fixture's name

File: tests/test_cart.py
Before:
```
import pytest


class TestCart:
    @pytest.fixture
    def db(self):
        return connect()

    def test_add(self, db):
        assert add(db) == 1
```
After:
```
import pytest


class TestCart:
    @pytest.fixture
    def db(self):
        if not HAVE_DB:
            pytest.skip("no db")
        return connect()

    def test_add(self, db):
        assert add(db) == 1
```
Listed: tests/test_cart.py::TestCart::db newly skipped

## A skip in a function nested in a test names the test

File: tests/test_cart.py
Before:
```
def test_add():
    assert add() == 1
```
After:
```
import pytest


def test_add():
    def needs_db():
        if not HAVE_DB:
            pytest.skip("no db")

    needs_db()
    assert add() == 1
```
Listed: tests/test_cart.py::test_add newly skipped

## A shared pytest skipif mark put on a test is listed, and a new test without it is not

File: tests/test_cart.py
Before:
```
import pytest

requires_db = pytest.mark.skipif(not HAVE_DB, reason="no db")


@requires_db
def test_add():
    assert add() == 1


def test_remove():
    assert remove() == 0
```
After:
```
import pytest

requires_db = pytest.mark.skipif(not HAVE_DB, reason="no db")


@requires_db
def test_add():
    assert add() == 1


@requires_db
def test_remove():
    assert remove() == 0


def test_total():
    assert total() == 0
```
Listed: tests/test_cart.py::test_remove newly skipped

## A shared pytest mark changed into a skip is listed under its name

File: tests/test_cart.py
Before:
```
import pytest

requires_db = pytest.mark.skipif(not HAVE_DB, reason="no db")


@requires_db
def test_add():
    assert add() == 1
```
After:
```
import pytest

requires_db = pytest.mark.skip(reason="broken")


@requires_db
def test_add():
    assert add() == 1
```
Listed: tests/test_cart.py::requires_db newly skipped

## A new shared pytest mark that no test uses is not listed

File: tests/test_cart.py
Before:
```
import pytest


def test_add():
    assert add() == 1
```
After:
```
import pytest

requires_db = pytest.mark.skipif(not HAVE_DB, reason="no db")


def test_add():
    assert add() == 1
```
Listed: nothing

## A pytestmark that names a shared mark skips the whole file

File: tests/test_cart.py
Before:
```
import pytest

requires_db = pytest.mark.skipif(not HAVE_DB, reason="no db")


def test_add():
    assert add() == 1
```
After:
```
import pytest

requires_db = pytest.mark.skipif(not HAVE_DB, reason="no db")
pytestmark = [requires_db]


def test_add():
    assert add() == 1
```
Listed: tests/test_cart.py newly skipped

## A test deleted from a test folder written in capitals is listed

File: Tests/cart.py
Before:
```
def test_add():
    assert add() == 1


def test_remove():
    assert remove() == 0
```
After:
```
def test_add():
    assert add() == 1
```
Listed: Tests/cart.py::test_remove deleted

## A Go file in a test folder that does not end in _test.go holds no tests

File: tests/helpers.go
Before:
```
package tests

import "testing"

func TestHelper(t *testing.T) {
	setUp(t)
}

func setUp(t *testing.T) {}
```
After:
```
package tests

func setUp() {}
```
Listed: nothing
